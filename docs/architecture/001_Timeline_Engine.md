# Timeline Engine v1.0

**Fase:** 4  
**Status:** Ativo  
**Dependências:** Astro Engine, Aspect Engine

## O que é

Motor temporal do Kalon Astro Engine.  
Percorre um intervalo de tempo em passos regulares e produz uma cronologia de eventos astronômicos.

## O que NÃO faz

- ❌ Não interpreta eventos
- ❌ Não responde perguntas
- ❌ Não conhece produtos Kalon
- ❌ Não usa lat/lon (trânsitos são universais)

## Interface pública

```python
from timeline.timeline_engine import generate

for event in generate(start, end, step="1d", filters=None):
    print(event["datetime"])
    print(event["planets"])
    print(event["aspects"])
```

## Parâmetros

- `start`, `end`: `datetime` — intervalo
- `step`: `"1d"`, `"12h"`, `"30m"` etc.
- `filters`: `{"objects": ["MOON","VEN"], "types": ["Trígono"], "phases": ["exact"]}`

## Schema de output por instante

```json
{
  "datetime": "2026-07-03T14:00:00",
  "planets": {
    "MOON": {"longitude": 314.38, "signo": "Aquário", "speed_longitude": 12.2}
  },
  "aspects": [
    {"id": "MOON_TRI_VEN", "tipo": "Trígono", "phase": "applying", "orbe": 0.3}
  ]
}
```

## Arquitetura

```
Timeline Engine
    ↓ chama
Astro Engine + Aspect Engine (Core v1.0)
    ↓ produz
Cronologia de eventos
    ↑ consumido por
Query Engine · Rule Engine · Produtos
```
