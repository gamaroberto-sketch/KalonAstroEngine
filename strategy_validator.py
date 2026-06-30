import yaml
import os
import unicodedata

ENGINE_VERSION_ATUAL = "1.0.0"
def _normalize_key(k: str) -> str:
    norm = unicodedata.normalize('NFKD', k).encode('ASCII', 'ignore').decode('utf-8').lower()
    return norm

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

def validar_vocabulario(cfg: dict) -> list[dict]:
    erros = []
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    aspects_path = os.path.join(base_dir, 'config', 'aspects.yaml')
    targets_path = os.path.join(base_dir, 'config', 'natal_targets.yaml')
    
    if not os.path.exists(aspects_path) or not os.path.exists(targets_path):
        return [{"codigo": "INTERNAL_ERROR", "mensagem": "Arquivos de dicionário não encontrados.", "severity": "error"}]
        
    with open(aspects_path, 'r', encoding='utf-8') as f:
        aspects_data = yaml.safe_load(f) or {}
        
    with open(targets_path, 'r', encoding='utf-8') as f:
        targets_data = yaml.safe_load(f) or {}
        
    # Build a set of valid aspect keys normalized
    valid_aspects = set()
    for k in aspects_data.get('aspects', {}).keys():
        norm = _normalize_key(k)
        valid_aspects.add(norm)
        if norm == 'oposicao':
            valid_aspects.add('opposicao')  # Trata o 'opposicao' (com 2 ps) legado
            
    valid_targets = targets_data.get('targets', {})
    
    tipo_estrategia = cfg.get('tipo', 'calendario_temporal')
    estrategias = cfg.get('calculo', {}).get('estrategias', {})
    
    for nome, est in estrategias.items():
        # Validar aspectos
        aspectos = est.get('aspectos', {})
        for asp in aspectos.keys():
            if _normalize_key(asp) not in valid_aspects:
                erros.append({
                    "codigo": "ASPECT_UNKNOWN",
                    "campo": asp,
                    "mensagem": f"Aspecto desconhecido '{asp}' na sub-estrategia '{nome}'",
                    "severity": "error"
                })
                
        # Validar alvo_natal
        alvo = est.get('alvo_natal')
        if alvo:
            if alvo not in valid_targets:
                erros.append({
                    "codigo": "TARGET_UNKNOWN",
                    "campo": alvo,
                    "mensagem": f"Alvo natal desconhecido '{alvo}' na sub-estrategia '{nome}'",
                    "severity": "error"
                })
            else:
                t_info = valid_targets[alvo]
                if not t_info.get('implementado', False):
                    erros.append({
                        "codigo": "TARGET_NOT_IMPLEMENTED",
                        "campo": alvo,
                        "mensagem": f"Alvo conhecido '{alvo}', porem ainda nao implementado.",
                        "severity": "warning"
                    })
                else:
                    disp = t_info.get('disponivel_para', [])
                    if tipo_estrategia not in disp:
                        erros.append({
                            "codigo": "TARGET_NOT_ALLOWED_FOR_TYPE",
                            "campo": alvo,
                            "mensagem": f"Alvo '{alvo}' nao disponivel para o tipo '{tipo_estrategia}'",
                            "severity": "error"
                        })
                        
    return erros

def validar_estrategia(cfg: dict) -> dict:
    erros_schema = []
    try:
        validar_schema_estrategia(cfg)
    except ValueError as e:
        erros_schema.append({"codigo": "INVALID_SCHEMA", "campo": None,
                              "mensagem": str(e), "severity": "error"})

    erros_vocab = validar_vocabulario(cfg)
    erros_engine = validar_engine_compatibilidade(cfg)
    erros_apresentacao = validar_apresentacao(cfg)

    todos = erros_schema + erros_vocab + erros_engine + erros_apresentacao
    tem_erro = any(e['severity'] == 'error' for e in todos)

    return {
        "valido": not tem_erro,
        "engine": {
            "compatibilidade": "ok" if not any(e['codigo'].startswith('ENGINE_VERSION') for e in erros_engine) else "incompativel",
            "versao": ENGINE_VERSION_ATUAL
        },
        "erros": [e for e in todos if e['severity'] == 'error'],
        "avisos": [e for e in todos if e['severity'] != 'error'],
        "resumo": {
            "schema": len(erros_schema) == 0,
            "vocabulario": len(erros_vocab) == 0,
            "engine": len(erros_engine) == 0,
            "apresentacao": len(erros_apresentacao) == 0
        }
    }

def _parse_semver(v: str) -> tuple:
    return tuple(int(x) for x in str(v).split('.'))

def validar_engine_compatibilidade(cfg: dict) -> list[dict]:
    erros = []
    engine = cfg.get('engine')
    if not engine:
        return erros
    
    v_min_str = engine.get('versao_minima')
    v_max_str = engine.get('versao_maxima')
    
    current = _parse_semver(ENGINE_VERSION_ATUAL)
    
    if v_min_str:
        v_min = _parse_semver(v_min_str)
        if v_min > current:
            erros.append({
                "codigo": "ENGINE_VERSION_TOO_LOW",
                "campo": "engine.versao_minima",
                "mensagem": f"Estrategia requer Engine >= {v_min_str}, mas Engine atual é {ENGINE_VERSION_ATUAL}",
                "severity": "error"
            })
            
    if v_max_str:
        v_max = _parse_semver(v_max_str)
        if current > v_max:
            erros.append({
                "codigo": "ENGINE_VERSION_TOO_HIGH",
                "campo": "engine.versao_maxima",
                "mensagem": f"Estrategia requer Engine <= {v_max_str}, mas Engine atual é {ENGINE_VERSION_ATUAL}",
                "severity": "error"
            })
            
    return erros

def validar_apresentacao(cfg: dict) -> list[dict]:
    erros = []
    
    estrategias = cfg.get('calculo', {}).get('estrategias', {})
    apresentacao = cfg.get('apresentacao', {})
    
    for nome, est in estrategias.items():
        aspectos_usados = est.get('aspectos', {}).keys()
        
        apres_est = apresentacao.get(nome, {})
        icones = apres_est.get('icones', {})
        cores = apres_est.get('cores', {})
        prioridades = apres_est.get('prioridades', {})
        
        icones_norm = {_normalize_key(k): v for k, v in icones.items()}
        cores_norm = {_normalize_key(k): v for k, v in cores.items()}
        prioridades_norm = {_normalize_key(k): v for k, v in prioridades.items()}
        
        for asp in aspectos_usados:
            asp_norm = _normalize_key(asp)
            if asp_norm not in icones_norm or asp_norm not in cores_norm or asp_norm not in prioridades_norm:
                erros.append({
                    "codigo": "INVALID_PRESENTATION",
                    "campo": f"{nome}.{asp}",
                    "mensagem": "Aspecto usado no calculo mas sem icone/cor/prioridade definidos na apresentacao",
                    "severity": "error"
                })
                
    return erros
