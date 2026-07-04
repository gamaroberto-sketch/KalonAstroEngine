import json
from fastapi.testclient import TestClient
from kalon_astro_api import app

client = TestClient(app)

def testar():
    payloads = [
        {
            "estrategia_id": "hair_corte",
            "nome": "Roberto",
            "data_nascimento": "1990-01-01",
            "hora_nascimento": "12:00",
            "cidade": "Ourinhos, SP",
            "data_inicio": "2026-07-01",
            "periodo_meses": 1
        },
        {
            "estrategia_id": "diet_metabolico",
            "nome": "Roberto",
            "data_nascimento": "1990-01-01",
            "hora_nascimento": "12:00",
            "cidade": "São Paulo, SP",
            "data_inicio": "2026-07-01",
            "periodo_meses": 1
        }
    ]
    
    for payload in payloads:
        print(f"\n=== TESTE AGENDA: {payload['estrategia_id']} ===")
        response = client.post("/api/v1/agenda", json=payload)
        res = response.json()
        
        # Omitir janelas para não sujar muito o log
        if 'janelas' in res:
            res['janelas'] = f"[{len(res['janelas'])} janelas calculadas...]"
            
        with open(f"agenda_result_{payload['estrategia_id']}.json", "w", encoding="utf-8") as f:
            json.dumps(res, indent=2, ensure_ascii=False)
            f.write(json.dumps(res, indent=2, ensure_ascii=False))
        
        print(f"Salvo: agenda_result_{payload['estrategia_id']}.json")

if __name__ == '__main__':
    testar()
