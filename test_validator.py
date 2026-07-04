import yaml
from strategy_validator import validar_vocabulario, validar_engine_compatibilidade, validar_apresentacao
import json

def testar():
    yamls = [
        "knowledge/strategies/hair/corte.yaml",
        "knowledge/strategies/diet/metabolico.yaml"
    ]
    
    for fpath in yamls:
        with open(fpath, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        
        e1 = validar_vocabulario(cfg)
        e2 = validar_engine_compatibilidade(cfg)
        e3 = validar_apresentacao(cfg)
        
        erros = e1 + e2 + e3
        
        print(f"=== Validando {fpath} ===")
        if not erros:
            print("OK! Lista vazia.")
        else:
            print(json.dumps(erros, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    testar()
