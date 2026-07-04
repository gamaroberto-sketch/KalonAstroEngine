import json
from astro_identity import montar_identity

def testar():
    natal_fake = {
      "sol": 156.4523,
      "lua": 234.1129,
      "mercurio": 140.9001,
      "venus": 165.3340,
      "marte": 180.2001,
      "jupiter": 90.0034,
      "saturno": 30.1234,
      "asc": 210.5678,
      "mc": 120.4500
    }
    
    resultado = montar_identity(
        natal=natal_fake,
        tradicao="classica",
        cidade="Ourinhos, SP",
        latitude=-22.983,
        longitude=-49.867,
        utc_offset="-03:00",
        strategy_id="hair_corte",
        strategy_versao="1.0.0"
    )
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    testar()
