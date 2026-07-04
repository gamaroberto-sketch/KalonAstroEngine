import yaml
import json
from fastapi.testclient import TestClient
from kalon_astro_api import app

client = TestClient(app)

import datetime
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def testar():
    yamls = [
        "knowledge/strategies/hair/corte.yaml",
        "knowledge/strategies/diet/metabolico.yaml"
    ]
    
    print("=== TESTE COM ARQUIVOS REAIS ===")
    for fpath in yamls:
        with open(fpath, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        
        # Converte datas pro json
        cfg_json = json.loads(json.dumps(cfg, cls=DateEncoder))
        
        response = client.post("/api/v1/validar-estrategia", json=cfg_json)
        print(f"-> {fpath}")
        res = response.json()
        print(f"Valido: {res['valido']}, Erros: {len(res['erros'])}, Avisos: {len(res['avisos'])}")

    print("\n=== TESTE COM YAML QUEBRADO ===")
    quebrado = """
id: teste_quebrado
tipo: calendario_temporal
suite: kalon_astro
modulo: test
nome: Teste Broken
versao: 1.0.0
engine:
  versao_minima: "99.0.0"  # Vai estourar versão
metadata: {}
calculo:
  estrategias:
    crescimento:
      alvo_natal: plutao  # Nao implementado
      aspectos: { aspecto_fake: 0, trigono: 120 }
apresentacao:
  crescimento:
    icones: { trigono: "x" }
    cores: { trigono: "red" }
    # Faltando prioridades e faltando config pro aspecto_fake
"""
    
    cfg_quebrado = yaml.safe_load(quebrado)
    response = client.post("/api/v1/validar-estrategia", json=cfg_quebrado)
    print("-> YAML Propositalmente Quebrado")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    print("\n=== TESTE COM BODY COMPLETAMENTE INVALIDO ===")
    bad_body = "isso não é yaml: : :".encode("utf-8")
    response = client.post(
        "/api/v1/validar-estrategia",
        content=bad_body,
        headers={"Content-Type": "application/x-yaml"}
    )
    print("-> Status Code:", response.status_code)
    print("-> Resposta:", response.json())

if __name__ == '__main__':
    testar()
