"""
KALON ASTRO — API Local v1.0
=============================
Roda em: uvicorn kalon_astro_api:app --reload --port 8000

Endpoint principal:
  POST /calcular
  Body: { nome, data_nascimento, hora_nascimento, cidade, data_inicio, periodo_meses }
  Return: { janelas: [...] }
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import swisseph as swe
import os, sys
import yaml
import unicodedata

app = FastAPI(title="Kalon Astro Engine", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STRATEGIES_DIR = os.path.join(BASE_DIR, 'knowledge', 'strategies')
I18N_DIR = os.path.join(BASE_DIR, 'knowledge', 'i18n')
MOTOR_VERSAO = "1.0.0"

def _normalizar_id(s: str) -> str:
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8').lower()

def carregar_i18n(idioma: str = 'pt-BR') -> dict:
    path = os.path.join(I18N_DIR, f'{idioma}.yaml')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)

def localizar_arquivo_estrategia(estrategia_id: str) -> str:
    for root, _, files in os.walk(STRATEGIES_DIR):
        for fname in files:
            if fname.endswith('.yaml'):
                fpath = os.path.join(root, fname)
                with open(fpath, encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                if data and data.get('id') == estrategia_id:
                    return fpath
    raise ValueError(f"Estratégia com id '{estrategia_id}' não encontrada")

from strategy_validator import validar_schema_estrategia, validar_estrategia

def carregar_estrategia(estrategia_id: str) -> dict:
    path = localizar_arquivo_estrategia(estrategia_id)
    with open(path, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    validar_schema_estrategia(cfg)
    return cfg

# Servir componentes estáticos (Agenda Kalon, CSS, JS)
_components_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'components')
if os.path.isdir(_components_path):
    app.mount("/components", StaticFiles(directory=_components_path), name="components")

# CORS — permite que o HTML local chame a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ephe_paths = [
    r'C:\KalonAstroEngine\ephe',          # Windows — pasta ephe no projeto
    r'C:\swisseph\ephe',                   # Windows — instalação global
    '/usr/share/ephe',                       # Linux
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ephe'),  # relativo
]
for _p in _ephe_paths:
    if os.path.isdir(_p):
        swe.set_ephe_path(_p)
        break
else:
    swe.set_ephe_path('')  # usa efemérides internas do pyswisseph (menos precisas mas funciona)

# ── MODELOS ───────────────────────────────────────────────────────────────────

class RequisicaoCalculo(BaseModel):
    nome: str
    data_nascimento: str        # "1957-08-29"
    hora_nascimento: str        # "00:00"
    cidade: str
    latitude: Optional[float] = None   # se não informada, usa lookup
    longitude: Optional[float] = None  # se não informada, usa lookup
    fuso_offset: Optional[int] = -3    # BRT padrão
    data_inicio: str            # "2026-07-29"
    periodo_meses: int = 1      # 1, 3, 6 ou 12

class RequisicaoAgenda(BaseModel):
    estrategia_id: str
    nome: str
    data_nascimento: str
    hora_nascimento: str
    cidade: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fuso_offset: Optional[int] = -3
    data_inicio: str
    periodo_meses: int = 1
    idioma: Optional[str] = 'pt-BR'

# ── LOOKUP DE CIDADES ─────────────────────────────────────────────────────────

def lookup_cidade(cidade: str):
    path = os.path.join(BASE_DIR, 'config', 'geocoding', 'cidades_br.yaml')
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    key_busca = _normalizar_id(cidade).strip()
    
    for cid_id, info in data.get('cidades', {}).items():
        nome_norm = _normalizar_id(info['nome'])
        display = f"{info['nome']}, {info.get('estado', info.get('pais', ''))}"
        display_norm = _normalizar_id(display)
        
        if key_busca in nome_norm or key_busca in display_norm:
            lat = info['latitude']
            lon = info['longitude']
            utc = info['utc_offset']
            fuso = int(utc.split(':')[0])
            return lat, lon, fuso
            
    raise ValueError(f"Cidade '{cidade}' não encontrada na base de dados.")

# ── CÁLCULO ASTRONÔMICO ───────────────────────────────────────────────────────

def datetime_para_jd(dt: datetime) -> float:
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute/60.0 + dt.second/3600.0)

def jd_para_local(jd: float, offset_h: int) -> datetime:
    ut = swe.jdut1_to_utc(jd, 1)
    dt = datetime(int(ut[0]), int(ut[1]), int(ut[2]),
                  int(ut[3]), int(ut[4]), int(ut[5]), tzinfo=timezone.utc)
    return dt + timedelta(hours=offset_h)

def diff_angular(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d

def calcular_natal(data_nasc: str, hora_nasc: str, lat: float, lon: float, fuso: int) -> dict:
    """Calcula posições natais via pyswisseph."""
    ano, mes, dia = map(int, data_nasc.split('-'))
    h, m = map(int, hora_nasc.split(':'))
    hora_local = h + m/60.0
    hora_utc = hora_local - fuso
    jd = swe.julday(ano, mes, dia, hora_utc)

    planetas = {
        'sol':      swe.SUN,
        'lua':      swe.MOON,
        'mercurio': swe.MERCURY,
        'venus':    swe.VENUS,
        'marte':    swe.MARS,
        'jupiter':  swe.JUPITER,
        'saturno':  swe.SATURN,
    }

    natal = {}
    for nome, pid in planetas.items():
        pos, _ = swe.calc_ut(jd, pid)
        natal[nome] = pos[0]

    # ASC
    casas, ascmc = swe.houses(jd, lat, lon, b'P')
    natal['asc'] = ascmc[0]
    natal['mc']  = ascmc[1]

    return natal

# ── ESTRATÉGIAS TEMPORAIS ─────────────────────────────────────────────────────

ESTRATEGIAS = {
    'crescimento': {
        'alvo_natal': 'jupiter',
        'aspectos': {'sextil': 60, 'trigono': 120},
        'plus': 'trigono',
        'label_cresc': '✂', 'label': 'Agende seu corte',
        'obj': 'Crescimento',
    },
    'beleza': {
        'alvo_natal': 'venus',
        'aspectos': {
            'conjuncao': 0, 'sextil': 60,
            'quadratura': 90, 'trigono': 120, 'opposicao': 180
        },
        'plus': 'conjuncao',
        'label': 'Agende seu corte',
        'obj': 'Beleza',
    },
    'vigor': {
        'alvo_natal': 'sol',
        'aspectos': {'conjuncao': 0, 'sextil': 60, 'trigono': 120},
        'plus': 'conjuncao',
        'label': 'Agende seu corte',
        'obj': 'Força',
    },
}

ORBE = 1.0
JANELA_H = 6  # 6h antes e 6h depois = 12h total
STEP_MIN = 10

SYM_MAP = {
    'crescimento': {'trigono': 'crown', 'sextil': 'ok'},
    'beleza':      {'conjuncao': 'star', 'trigono': 'star', 'sextil': 'ok',
                    'quadratura': 'warn', 'opposicao': 'warn'},
    'vigor':       {'conjuncao': 'star', 'trigono': 'star', 'sextil': 'ok'},
}

def calcular_janelas_legacy(natal: dict, data_inicio: str, periodo_meses: int, fuso: int) -> list:
    """Calcula todas as janelas temporais para o período."""
    dt_ini = datetime.fromisoformat(data_inicio + 'T00:00:00').replace(tzinfo=timezone.utc)
    dt_fim = dt_ini.replace(month=((dt_ini.month - 1 + periodo_meses) % 12) + 1)
    if periodo_meses >= 12:
        dt_fim = dt_ini.replace(year=dt_ini.year + 1)
    elif dt_ini.month + periodo_meses > 12:
        dt_fim = dt_ini.replace(year=dt_ini.year + 1,
                                month=(dt_ini.month + periodo_meses) % 12 or 12)
    else:
        dt_fim = dt_ini.replace(month=dt_ini.month + periodo_meses)

    step = timedelta(minutes=STEP_MIN)
    resultados = {}  # data → {cresc, beleza, vigor}

    for nome_est, est in ESTRATEGIAS.items():
        alvo_lon = natal[est['alvo_natal']]
        em_asp = {}
        dt = dt_ini

        while dt < dt_fim:
            jd = datetime_para_jd(dt)
            pos, _ = swe.calc_ut(jd, swe.MOON)
            lon_lua = pos[0]
            diff = diff_angular(lon_lua, alvo_lon)

            for nome_asp, angulo in est['aspectos'].items():
                orbe = abs(diff - angulo)
                if orbe <= ORBE:
                    if nome_asp not in em_asp or orbe < em_asp[nome_asp]['orbe']:
                        em_asp[nome_asp] = {'jd': jd, 'orbe': orbe, 'asp': nome_asp}
                else:
                    if nome_asp in em_asp:
                        ev = em_asp.pop(nome_asp)
                        local_pico = jd_para_local(ev['jd'], fuso)
                        local_ini  = jd_para_local(ev['jd'] - JANELA_H/24, fuso)
                        local_fim  = jd_para_local(ev['jd'] + JANELA_H/24, fuso)

                        chave = local_pico.strftime('%Y-%m-%d')
                        if chave not in resultados:
                            resultados[chave] = {
                                'date_key': chave,
                                'day':   local_pico.strftime('%d'),
                                'mon':   local_pico.strftime('%b').upper()[:3],
                                'pico':  local_pico.strftime('%H:%M'),
                                'inicio':local_ini.strftime('%H:%M'),
                                'fim':   local_fim.strftime('%H:%M'),
                                'cresc': 'dash', 'forca': 'dash', 'beleza': 'dash',
                                'objs':  [],
                                'classe': '',
                                'ast_cresc': None, 'ast_forca': None, 'ast_beleza': None,
                                'porque_cresc': '', 'porque_forca': '', 'porque_beleza': '',
                                'qualidades_cresc': [], 'qualidades_forca': [], 'qualidades_beleza': [],
                            }

                        sim = SYM_MAP[nome_est].get(ev['asp'], 'ok')
                        ast_info = {
                            'lua': f"{lon_lua:.1f}°",
                            'natal': f"{alvo_lon:.2f}° ({est['alvo_natal']})",
                            'aspecto': ev['asp'].capitalize(),
                            'orbe': f"{ev['orbe']:.2f}°",
                            'aplic': 'Aplicante',
                            'est': f"Lua → {est['alvo_natal']} natal · {', '.join(est['aspectos'].keys())}",
                        }

                        if nome_est == 'crescimento':
                            resultados[chave]['cresc'] = sim
                            resultados[chave]['ast_cresc'] = ast_info
                        elif nome_est == 'beleza':
                            resultados[chave]['beleza'] = sim
                            resultados[chave]['ast_beleza'] = ast_info
                        elif nome_est == 'vigor':
                            resultados[chave]['forca'] = sim
                            resultados[chave]['ast_forca'] = ast_info

                        if est['obj'] not in resultados[chave]['objs']:
                            resultados[chave]['objs'].append(est['obj'])

            dt += step

    # Montar lista ordenada e calcular campos derivados
    MESES_PT = {'JAN':'JAN','FEB':'FEV','MAR':'MAR','APR':'ABR','MAY':'MAI',
                'JUN':'JUN','JUL':'JUL','AUG':'AGO','SEP':'SET','OCT':'OUT',
                'NOV':'NOV','DEC':'DEZ'}

    lista = []
    for chave in sorted(resultados.keys()):
        r = resultados[chave]
        # Corrigir mês para português
        r['mon'] = MESES_PT.get(r['mon'], r['mon'])
        # Determinar classe CSS
        if all(v == 'dash' for v in [r['cresc'], r['forca'], r['beleza']]):
            continue  # ignorar dias sem evento
        objs_str = ' + '.join(r['objs']) if r['objs'] else '—'
        r['objs'] = objs_str
        # Crown para o melhor dia (todos três ativos com boa intensidade)
        n_bons = sum(1 for v in [r['cresc'], r['forca'], r['beleza']] if v in ('star','crown','ok'))
        if n_bons == 3 and 'crown' not in [r['cresc'], r['forca'], r['beleza']]:
            r['cresc'] = 'crown'
        # Campos unificados para o frontend
        r['ast'] = {'lua':'—','natal':'—','aspecto':'—','orbe':'—','aplic':'—','est':'—'}
        r['porque'] = '—'
        r['qualidades'] = []
        for tipo in ['cresc', 'forca', 'beleza']:
            if r.get(f'ast_{tipo}') is not None:
                r['ast']        = r[f'ast_{tipo}']
                r['porque']     = r[f'porque_{tipo}'] or f"Aspecto da Lua com ponto natal ({tipo})."
                r['qualidades'] = r[f'qualidades_{tipo}'] or ["momento favorável"]
                break
        lista.append(r)

    return lista


def calcular_janelas(natal: dict, data_inicio: str, periodo_meses: int, fuso: int, calculo_cfg: dict) -> list:
    """Calcula janelas temporais baseadas no calculo_cfg da estratégia."""
    dt_ini = datetime.fromisoformat(data_inicio + 'T00:00:00').replace(tzinfo=timezone.utc)
    dt_fim = dt_ini.replace(month=((dt_ini.month - 1 + periodo_meses) % 12) + 1)
    if periodo_meses >= 12:
        dt_fim = dt_ini.replace(year=dt_ini.year + 1)
    elif dt_ini.month + periodo_meses > 12:
        dt_fim = dt_ini.replace(year=dt_ini.year + 1,
                                month=(dt_ini.month + periodo_meses) % 12 or 12)
    else:
        dt_fim = dt_ini.replace(month=dt_ini.month + periodo_meses)

    step = timedelta(minutes=STEP_MIN)
    resultados = {}

    for nome_sub, est in calculo_cfg['estrategias'].items():
        alvo_lon = natal[est['alvo_natal']]
        janela_h = est.get('janela_h', 6)
        em_asp = {}
        dt = dt_ini

        while dt < dt_fim:
            jd = datetime_para_jd(dt)
            pos, _ = swe.calc_ut(jd, swe.MOON)
            lon_lua = pos[0]
            diff = diff_angular(lon_lua, alvo_lon)

            for nome_asp, angulo in est['aspectos'].items():
                orbe = abs(diff - angulo)
                if orbe <= ORBE:
                    if nome_asp not in em_asp or orbe < em_asp[nome_asp]['orbe']:
                        em_asp[nome_asp] = {'jd': jd, 'orbe': orbe, 'asp': nome_asp}
                else:
                    if nome_asp in em_asp:
                        ev = em_asp.pop(nome_asp)
                        local_pico = jd_para_local(ev['jd'], fuso)
                        local_ini  = jd_para_local(ev['jd'] - janela_h/24, fuso)
                        local_fim  = jd_para_local(ev['jd'] + janela_h/24, fuso)

                        chave = local_pico.strftime('%Y-%m-%d')
                        if chave not in resultados:
                            resultados[chave] = {
                                'date_key': chave,
                                'day':   local_pico.strftime('%d'),
                                'mon':   local_pico.strftime('%b').upper()[:3],
                                'pico':  local_pico.strftime('%H:%M'),
                                'inicio':local_ini.strftime('%H:%M'),
                                'fim':   local_fim.strftime('%H:%M'),
                                'campos': {}
                            }

                        resultados[chave]['campos'][nome_sub] = {
                            'aspecto': ev['asp'],
                            'orbe': f"{ev['orbe']:.2f}°",
                            'lua': f"{lon_lua:.1f}°",
                            'natal': f"{alvo_lon:.2f}° ({est['alvo_natal']})",
                            'aplic': 'Aplicante' if ev['asp'] else ''
                        }
            dt += step

    MESES_PT = {'JAN':'JAN','FEB':'FEV','MAR':'MAR','APR':'ABR','MAY':'MAI',
                'JUN':'JUN','JUL':'JUL','AUG':'AGO','SEP':'SET','OCT':'OUT',
                'NOV':'NOV','DEC':'DEZ'}

    lista = []
    for chave in sorted(resultados.keys()):
        r = resultados[chave]
        r['mon'] = MESES_PT.get(r['mon'], r['mon'])
        lista.append(r)

    return lista

def aplicar_apresentacao(janelas: list, apresentacao_cfg: dict, i18n: dict) -> list:
    for j in janelas:
        for nome_sub, dados in j['campos'].items():
            apres = apresentacao_cfg.get(nome_sub, {})
            icone_map = apres.get('icones', {})
            cor_map = apres.get('cores', {})
            prioridade_map = apres.get('prioridades', {})

            dados['icone'] = icone_map.get(dados['aspecto'], '—')      # já o glifo pronto
            dados['cor'] = cor_map.get(dados['aspecto'], 'dim')
            dados['prioridade'] = prioridade_map.get(dados['aspecto'], 'baixa')
            label_key = apres.get('label', nome_sub)
            dados['label'] = i18n.get(label_key, label_key)

            dados['auditoria'] = [
                {
                    "titulo": "Cálculo Astronômico",
                    "itens": [
                        {"label": "Aspecto", "valor": dados['aspecto'].capitalize()},
                        {"label": "Orbe", "valor": dados['orbe']},
                        {"label": "Lua", "valor": dados['lua']},
                        {"label": "Natal", "valor": dados['natal']},
                        {"label": "Aplicação", "valor": dados['aplic']},
                    ]
                }
            ]
    return janelas

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.get("/ping")
def ping():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home():
    """Serve o AstroHair diretamente — sem problemas de CORS."""
    import os
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astro_hair_v8.html")
    if os.path.exists(html_path):
        with open(html_path, encoding="utf-8") as f:
            return f.read()
    return "<h1>Copie astro_hair_v8.html para C:\KalonAstroEngine\</h1>"

@app.get("/diet", response_class=HTMLResponse)
def diet_page():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astro_diet_v1.html")
    if os.path.exists(html_path):
        with open(html_path, encoding="utf-8") as f:
            return f.read()
    return "<h1>astro_diet_v1.html não encontrado</h1>"

@app.post("/calcular")
def calcular(req: RequisicaoCalculo):
    # Coordenadas
    if req.latitude and req.longitude:
        lat, lon, fuso = req.latitude, req.longitude, req.fuso_offset
    else:
        lat, lon, fuso = lookup_cidade(req.cidade)

    # Mapa natal
    natal = calcular_natal(req.data_nascimento, req.hora_nascimento, lat, lon, fuso)

    # Janelas temporais
    janelas = calcular_janelas_legacy(natal, req.data_inicio, req.periodo_meses, fuso)

    return {
        "nome": req.nome,
        "cidade": req.cidade,
        "periodo_meses": req.periodo_meses,
        "data_inicio": req.data_inicio,
        "total_janelas": len(janelas),
        "natal": {k: round(v, 4) for k, v in natal.items()},
        "janelas": janelas,
    }

from astro_identity import montar_identity, formatar_utc_offset

@app.post("/api/v1/agenda")
def agenda(req: RequisicaoAgenda):
    cfg = carregar_estrategia(req.estrategia_id)
    i18n = carregar_i18n(req.idioma)
    lat, lon, fuso = (req.latitude, req.longitude, req.fuso_offset) if req.latitude else lookup_cidade(req.cidade)
    natal = calcular_natal(req.data_nascimento, req.hora_nascimento, lat, lon, fuso)
    janelas = calcular_janelas(natal, req.data_inicio, req.periodo_meses, fuso, cfg['calculo'])
    janelas = aplicar_apresentacao(janelas, cfg['apresentacao'], i18n)

    identity = montar_identity(
        natal=natal,
        tradicao="classica",
        cidade=req.cidade,
        latitude=lat,
        longitude=lon,
        utc_offset=formatar_utc_offset(fuso),
        strategy_id=cfg.get('id'),
        strategy_versao=cfg.get('versao')
    )

    return {
        "estrategia_id": req.estrategia_id,
        "estrategia_nome": cfg['nome'],
        "versao": cfg['versao'],
        "motor_temporal": MOTOR_VERSAO,
        "calculado_em": datetime.now(timezone.utc).isoformat(),
        "o_que_e": cfg.get('o_que_e'),
        "como_usar": cfg.get('como_usar'),
        "legenda": cfg.get('legenda'),
        "observacoes": cfg.get('observacoes'),
        "nome": req.nome,
        "janelas": janelas,
        "natal": {k: round(v,4) for k,v in natal.items()},
        "identity": identity["identity"],
    }

@app.post("/api/v1/validar-estrategia")
async def validar_estrategia_endpoint(request: Request):
    body_bytes = await request.body()
    body = None
    try:
        import json
        body = json.loads(body_bytes)
    except json.JSONDecodeError:
        try:
            import yaml
            body = yaml.safe_load(body_bytes)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400,
                detail=f"Corpo da requisição não é JSON nem YAML válido: {str(e)}")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400,
            detail="Corpo da requisição deve ser um objeto/dicionário válido")
    resultado = validar_estrategia(body)
    return resultado

@app.get("/api/v1/vocabulario/aspectos")
def get_aspectos():
    """Retorna lista de aspectos válidos do Engine para uso no Builder."""
    path = os.path.join(BASE_DIR, 'config', 'aspects.yaml')
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    # Retornar lista com nome (chave do yaml), angulo, orbe e harmonico
    aspectos = []
    for nome, info in data.get('aspects', {}).items():
        aspectos.append({
            "id": _normalizar_id(nome),
            "nome": nome,
            "angulo": info.get('angulo', info.get('angle', 0)),
            "orbe": info.get('orbe', info.get('orb', 1)),
            "harmonico": info.get('harmonico', info.get('harmonic', True))
        })
    return {"aspectos": aspectos}

@app.get("/api/v1/vocabulario/alvos")
def get_alvos():
    """Retorna lista de alvos natais válidos do Engine para uso no Builder."""
    path = os.path.join(BASE_DIR, 'config', 'natal_targets.yaml')
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    alvos = []
    for nome, info in data.get('targets', {}).items():
        alvos.append({
            "id": nome,
            "tipo": info.get('tipo', ''),
            "implementado": info.get('implementado', False),
            "descricao": info.get('descricao', ''),
            "disponivel_para": info.get('disponivel_para', [])
        })
    return {"alvos": alvos}

@app.get("/api/v1/vocabulario/suites")
def get_suites():
    path = os.path.join(BASE_DIR, 'config', 'suites.yaml')
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    resultado = []
    for suite_id, suite_info in data.get('suites', {}).items():
        modulos = []
        for mod_id, mod_info in suite_info.get('modulos', {}).items():
            modulos.append({
                "id": mod_id,
                "nome": mod_info.get('nome', ''),
                "descricao": mod_info.get('descricao', ''),
                "status": mod_info.get('status', 'planned'),
                "categoria_legado": mod_info.get('categoria_legado', mod_id)
            })
        resultado.append({
            "id": suite_id,
            "nome": suite_info.get('nome', ''),
            "descricao": suite_info.get('descricao', ''),
            "status": suite_info.get('status', 'active'),
            "modulos": modulos
        })
    return {"suites": resultado}

@app.get("/api/v1/cidades")
def get_cidades():
    """Retorna lista de cidades da Base Kalon para autocomplete."""
    path = os.path.join(BASE_DIR, 'config', 'geocoding', 'cidades_br.yaml')
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    cidades = []
    for cid_id, info in data.get('cidades', {}).items():
        cidades.append({
            "id": cid_id,
            "nome": info['nome'],
            "estado": info.get('estado', ''),
            "display": f"{info['nome']}, {info.get('estado', info.get('pais', ''))}"
        })
    cidades.sort(key=lambda x: x['display'])
    return {"cidades": cidades, "total": len(cidades)}

@app.get("/tools/builder", response_class=HTMLResponse)
def builder_page():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "builder.html")
    if os.path.exists(html_path):
        with open(html_path, encoding="utf-8") as f:
            return f.read()
    return "<h1>builder.html não encontrado</h1>"

@app.get("/api/v1/estrategias")
def get_estrategias():
    """Lista todas as estratégias disponíveis no Engine."""
    estrategias = []
    for root, dirs, files in os.walk(STRATEGIES_DIR):
        for fname in files:
            if fname.endswith('.yaml'):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, encoding='utf-8') as f:
                        cfg = yaml.safe_load(f)
                    estrategias.append({
                        "id": cfg.get('id'),
                        "nome": cfg.get('nome'),
                        "descricao": cfg.get('descricao', ''),
                        "suite": cfg.get('suite', cfg.get('categoria', '')),
                        "modulo": cfg.get('modulo', ''),
                        "versao": cfg.get('versao', '1.0.0'),
                        "status": cfg.get('metadata', {}).get('status', 'production')
                    })
                except Exception as e:
                    pass  # ignora arquivos corrompidos silenciosamente
    estrategias.sort(key=lambda x: x.get('nome', ''))
    return {"estrategias": estrategias, "total": len(estrategias)}

@app.get("/kalon", response_class=HTMLResponse)
def launcher_page():
    html_path = os.path.join(BASE_DIR, "kalon_launcher.html")
    if os.path.exists(html_path):
        with open(html_path, encoding="utf-8") as f:
            return f.read()
    return "<h1>kalon_launcher.html não encontrado</h1>"

