import yaml, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strategy_validator import validar_estrategia

TESTS = [
    # (arquivo, categoria_esperada, codigo_esperado_ou_None)
    ('tests/validator/valid/hair_corte.yaml', 'valid', None),
    ('tests/validator/valid/diet_metabolico.yaml', 'valid', None),
    ('tests/validator/invalid/unknown_aspect.yaml', 'invalid', 'ASPECT_UNKNOWN'),
    ('tests/validator/invalid/unknown_target.yaml', 'invalid', 'TARGET_UNKNOWN'),
    ('tests/validator/invalid/invalid_schema.yaml', 'invalid', 'INVALID_SCHEMA'),
    ('tests/validator/invalid/invalid_presentation.yaml', 'invalid', 'INVALID_PRESENTATION'),
    ('tests/validator/invalid/incompatible_engine.yaml', 'invalid', 'ENGINE_VERSION_TOO_LOW'),
    ('tests/validator/warnings/urano_not_implemented.yaml', 'warning', 'TARGET_NOT_IMPLEMENTED'),
    ('tests/validator/warnings/netuno_not_implemented.yaml', 'warning', 'TARGET_NOT_IMPLEMENTED'),
    ('tests/validator/warnings/plutao_not_implemented.yaml', 'warning', 'TARGET_NOT_IMPLEMENTED'),
]

def run():
    total = len(TESTS)
    passed = 0
    for path, categoria, codigo in TESTS:
        with open(path, encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        resultado = validar_estrategia(cfg)
        
        ok = False
        if categoria == 'valid':
            ok = resultado['valido'] == True and len(resultado['erros']) == 0
        elif categoria == 'invalid':
            ok = resultado['valido'] == False
            if codigo:
                ok = ok and any(e['codigo'] == codigo for e in resultado['erros'])
        elif categoria == 'warning':
            ok = resultado['valido'] == True  # warnings não bloqueiam
            if codigo:
                ok = ok and any(a['codigo'] == codigo for a in resultado['avisos'])
        
        status = '✔' if ok else '✘'
        if ok:
            passed += 1
        print(f"{status} [{categoria.upper():8}] {os.path.basename(path)}"
              + (f" — esperado: {codigo}" if codigo else ""))
    
    print(f"\nTOTAL: {passed}/{total} aprovados")
    sys.exit(0 if passed == total else 1)

if __name__ == '__main__':
    run()
