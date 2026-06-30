import os
import yaml
from datetime import datetime

SIGNOS = ['aries', 'touro', 'gemeos', 'cancer', 'leao', 'virgem', 'libra',
          'escorpiao', 'sagitario', 'capricornio', 'aquario', 'peixes']

NOMES_EXIBICAO = {
    'aries': 'Áries', 'touro': 'Touro', 'gemeos': 'Gêmeos', 'cancer': 'Câncer',
    'leao': 'Leão', 'virgem': 'Virgem', 'libra': 'Libra', 'escorpiao': 'Escorpião',
    'sagitario': 'Sagitário', 'capricornio': 'Capricórnio', 'aquario': 'Aquário',
    'peixes': 'Peixes'
}

NOMES_PLANETAS = {
    'sol': 'Sol', 'lua': 'Lua', 'mercurio': 'Mercúrio', 'venus': 'Vênus',
    'marte': 'Marte', 'jupiter': 'Júpiter', 'saturno': 'Saturno',
    'urano': 'Urano', 'netuno': 'Netuno', 'plutao': 'Plutão'
}

def _grau_para_signo(longitude: float) -> dict:
    indice_signo = int(longitude // 30) % 12
    signo = SIGNOS[indice_signo]
    grau_no_signo = longitude % 30
    grau = int(grau_no_signo)
    resto_min = (grau_no_signo - grau) * 60
    minuto = int(resto_min)
    segundo = int((resto_min - minuto) * 60)
    texto = f"{NOMES_EXIBICAO[signo]} {grau:02d}°{minuto:02d}'"
    
    return {
        "longitude": round(longitude, 4),
        "signo": signo,
        "indice_signo": indice_signo,
        "grau": grau,
        "minuto": minuto,
        "segundo": segundo,
        "texto": texto
    }

def _gerar_report_id() -> str:
    hoje = datetime.now().strftime("%Y%m%d")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    counter_file = os.path.join(base_dir, '.ka_report_counter')
    
    contador = 1
    if os.path.exists(counter_file):
        with open(counter_file, 'r', encoding='utf-8') as f:
            try:
                data = f.read().strip().split('-')
                if len(data) == 2 and data[0] == hoje:
                    contador = int(data[1]) + 1
            except (ValueError, IndexError):
                pass
                
    with open(counter_file, 'w', encoding='utf-8') as f:
        f.write(f"{hoje}-{contador}")
        
    return f"KA-{hoje}-{contador:06d}"

def montar_identity(natal: dict, tradicao: str = "classica", cidade: str = None,
                    latitude: float = None, longitude: float = None,
                    utc_offset: str = None, strategy_id: str = None,
                    strategy_versao: str = None) -> dict:
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Carregar metadados
    with open(os.path.join(base_dir, 'config', 'sign_metadata.yaml'), 'r', encoding='utf-8') as f:
        sign_meta = yaml.safe_load(f).get('signos', {})
        
    with open(os.path.join(base_dir, 'config', 'natal_targets.yaml'), 'r', encoding='utf-8') as f:
        targets_meta = yaml.safe_load(f).get('targets', {})
        
    identity_map = {}
    
    for ponto, lon in natal.items():
        dados = _grau_para_signo(lon)
        
        # Logica exclusiva do ASC para regente
        if ponto == 'asc':
            s_nome = dados['signo']
            s_data = sign_meta.get(s_nome, {})
            
            reg_classicos = s_data.get('classica', {}).get('regentes', [])
            reg_modernos = s_data.get('moderna', {}).get('regentes', [])
            
            moderno_impl = []
            for r in reg_modernos:
                impl = targets_meta.get(r, {}).get('implementado', False)
                moderno_impl.append(impl)
                
            dados['regente_do_ascendente'] = {
                "classico": [NOMES_PLANETAS.get(r, r.capitalize()) for r in reg_classicos],
                "moderno": [NOMES_PLANETAS.get(r, r.capitalize()) for r in reg_modernos],
                "moderno_implementado": moderno_impl
            }
            
        identity_map[ponto] = dados
        
    identity_map['sistema_casas'] = "Placidus"
    identity_map['zodiaco'] = "Tropical"
    identity_map['efemerides'] = "Swiss Ephemeris"
    identity_map['tradicao'] = tradicao
    identity_map['local'] = {
        "cidade": cidade,
        "latitude": latitude,
        "longitude": longitude,
        "utc": utc_offset
    }
    
    # Engine fallback 1.0.0
    engine_ver = "1.0.0"
    try:
        from strategy_validator import ENGINE_VERSION_ATUAL
        engine_ver = ENGINE_VERSION_ATUAL
    except ImportError:
        pass
    identity_map['engine'] = engine_ver
    
    if strategy_id:
        identity_map['strategy'] = f"{strategy_id} {strategy_versao}" if strategy_versao else strategy_id
    else:
        identity_map['strategy'] = None
        
    identity_map['report_id'] = _gerar_report_id()
    
    return {"identity": identity_map}
