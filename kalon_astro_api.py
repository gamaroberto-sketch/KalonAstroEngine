"""
KALON ASTRO — API Local v1.0
=============================
Roda em: uvicorn kalon_astro_api:app --reload --port 8000

Endpoint principal:
  POST /calcular
  Body: { nome, data_nascimento, hora_nascimento, cidade, data_inicio, periodo_meses }
  Return: { janelas: [...] }
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import swisseph as swe
import os, sys
import yaml

app = FastAPI(title="Kalon Astro Engine", version="1.0.0")

STRATEGIES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge', 'strategies')
I18N_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge', 'i18n')
MOTOR_VERSAO = "1.0.0"

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

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge', 'schema', 'estrategia.schema.yaml')

def validar_schema_estrategia(cfg: dict):
    if not os.path.exists(SCHEMA_PATH):
        raise ValueError(f"Schema não encontrado: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, encoding='utf-8') as f:
        schema = yaml.safe_load(f)
        
    obrigatorios = schema.get('fields', {}).get('required', [])
    faltando = [c for c in obrigatorios if c not in cfg]
    if faltando:
        raise ValueError(f"Estratégia '{cfg.get('id','?')}' inválida — campos faltando: {faltando}")
        
    has_suite = 'suite' in cfg
    has_modulo = 'modulo' in cfg
    if has_suite != has_modulo:
        raise ValueError(f"Estratégia '{cfg.get('id','?')}' inválida — 'suite' e 'modulo' devem ser informados juntos.")
        
    has_categoria = 'categoria' in cfg
    if not (has_suite or has_categoria):
        raise ValueError(f"Estratégia '{cfg.get('id','?')}' inválida — requer 'suite' e 'modulo', ou 'categoria'")
        
    # Validar engine
    if 'engine' in cfg:
        engine_opt = schema.get('structures', {}).get('engine', {}).get('optional', [])
        desconhecidos = [k for k in cfg['engine'] if k not in engine_opt]
        if desconhecidos:
            raise ValueError(f"Estratégia '{cfg.get('id','?')}' inválida — campos desconhecidos em 'engine': {desconhecidos}")

    # Validar metadata
    if 'metadata' in cfg:
        meta_opt = schema.get('structures', {}).get('metadata', {}).get('optional', [])
        desconhecidos = [k for k in cfg['metadata'] if k not in meta_opt]
        if desconhecidos:
            raise ValueError(f"Estratégia '{cfg.get('id','?')}' inválida — campos desconhecidos em 'metadata': {desconhecidos}")
        
    # Validar calculo.estrategias
    calc_req = schema.get('structures', {}).get('calculo_estrategia', {}).get('required', [])
    for nome, est in cfg.get('calculo', {}).get('estrategias', {}).items():
        faltando_calc = [c for c in calc_req if c not in est]
        if faltando_calc:
            raise ValueError(f"Estratégia '{cfg.get('id','?')}' inválida — calculo '{nome}' com campos faltando: {faltando_calc}")

    # Validar apresentacao
    apres_req = schema.get('structures', {}).get('apresentacao_estrategia', {}).get('required', [])
    for nome, apres in cfg.get('apresentacao', {}).items():
        faltando_apres = [c for c in apres_req if c not in apres]
        if faltando_apres:
            raise ValueError(f"Estratégia '{cfg.get('id','?')}' inválida — apresentacao '{nome}' com campos faltando: {faltando_apres}")

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

CIDADES = {
    "ourinhos, sp":      (-22.983, -49.867, -3),
    "são paulo, sp":     (-23.550, -46.633, -3),
    "rio de janeiro, rj":(-22.906, -43.172, -3),
    "belo horizonte, mg":(-19.920, -43.938, -3),
    "curitiba, pr":      (-25.429, -49.271, -3),
    "porto alegre, rs":  (-30.033, -51.230, -3),
    "salvador, ba":      (-12.971, -38.501, -3),
    "fortaleza, ce":     (-3.717,  -38.543, -3),
    "recife, pe":        (-8.054,  -34.881, -3),
    "manaus, am":        (-3.119,  -60.021, -4),
    "belém, pa":         (-1.455,  -48.502, -3),
    "goiânia, go":       (-16.686, -49.264, -3),
    "brasília, df":      (-15.779, -47.929, -3),
    "campinas, sp":      (-22.906, -47.063, -3),
    "guarulhos, sp":     (-23.453, -46.533, -3),
    "são bernardo do campo, sp": (-23.694, -46.565, -3),
    "nova iguaçu, rj":   (-22.759, -43.450, -3),
    "maceió, al":        (-9.666,  -35.735, -3),
    "natal, rn":         (-5.793,  -35.209, -3),
    "teresina, pi":      (-5.092,  -42.803, -3),
    "campo grande, ms":  (-20.469, -54.620, -4),
    "joão pessoa, pb":   (-7.115,  -34.861, -3),
    "santos, sp":        (-23.961, -46.333, -3),
    "londrina, pr":      (-23.304, -51.168, -3),
    "cuiabá, mt":        (-15.596, -56.096, -4),
    "macapá, ap":        (0.034,   -51.066, -3),
    "porto velho, ro":   (-8.761,  -63.900, -4),
    "boa vista, rr":     (2.820,   -60.673, -4),
    "rio branco, ac":    (-9.975,  -67.810, -5),
    "palmas, to":        (-10.249, -48.324, -3),
    "florianópolis, sc": (-27.595, -48.548, -3),
    "vitória, es":       (-20.319, -40.338, -3),
    "maringá, pr":       (-23.425, -51.938, -3),
    "joinville, sc":     (-26.303, -48.846, -3),
    "sorocaba, sp":      (-23.501, -47.458, -3),
    "ribeirão preto, sp":(-21.177, -47.810, -3),
    "uberlândia, mg":    (-18.919, -48.277, -3),
    "juiz de fora, mg":  (-21.764, -43.350, -3),
    "contagem, mg":      (-19.932, -44.053, -3),
    "feira de santana, ba":(-12.267,-38.967,-3),
    "aracaju, se":       (-10.909, -37.072, -3),
    "caucaia, ce":       (-3.737,  -38.658, -3),
    "são luís, ma":      (-2.539,  -44.282, -3),
    "mogi das cruzes, sp":(-23.523,-46.185,-3),
    "betim, mg":         (-19.968, -44.198, -3),
    "jundiaí, sp":       (-23.186, -46.884, -3),
    "são josé dos campos, sp":(-23.178,-45.886,-3),
    "carapicuíba, sp":   (-23.522, -46.836, -3),
    "piracicaba, sp":    (-22.728, -47.649, -3),
    "osasco, sp":        (-23.532, -46.791, -3),
}

def lookup_cidade(cidade: str):
    key = cidade.lower().strip()
    if key in CIDADES:
        lat, lon, fuso = CIDADES[key]
        return lat, lon, fuso
    # Busca parcial
    for k, v in CIDADES.items():
        if key in k or k in key:
            return v
    return -23.55, -46.63, -3  # São Paulo como fallback

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

@app.post("/api/v1/agenda")
def agenda(req: RequisicaoAgenda):
    cfg = carregar_estrategia(req.estrategia_id)
    i18n = carregar_i18n(req.idioma)
    lat, lon, fuso = (req.latitude, req.longitude, req.fuso_offset) if req.latitude else lookup_cidade(req.cidade)
    natal = calcular_natal(req.data_nascimento, req.hora_nascimento, lat, lon, fuso)
    janelas = calcular_janelas(natal, req.data_inicio, req.periodo_meses, fuso, cfg['calculo'])
    janelas = aplicar_apresentacao(janelas, cfg['apresentacao'], i18n)

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
    }

