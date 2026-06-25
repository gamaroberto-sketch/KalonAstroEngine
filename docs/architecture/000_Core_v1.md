# Core v1.0 — Constituição do Kalon Astro Engine

**Congelado em:** 25 de junho de 2026  
**Validado contra:** SolarFire Gold — mapa Roberto Gama 29/08/1957 00:00 Ourinhos SP  
**Testes:** 28/28 automáticos · 13/13 Astro Doctor  
**Tag Git:** `core-v1.0`

---

## O que é o Core

O Core é o núcleo astronômico do Kalon Astro Engine.  
Ele não interpreta. Não recomenda. Não pondera.  
Ele **calcula**.

Qualquer informação que sair do Core é matematicamente verificável contra efemérides publicadas.

---

## O que o Core faz

### Astro Engine (`core/astro_engine.py`)
- Recebe: data, hora, latitude, longitude, fuso horário
- Calcula: posições de 10 planetas (Sol a Plutão), Ascendente, MC, 12 casas (Placidus)
- Expõe por planeta: longitude, signo, grau, minuto, segundo, velocidade real (graus/dia), retrógrado
- Aplica DeltaT (Ephemeris Time) nos planetas; casas calculadas em UT
- Precisão validada: diferença máxima de 1'' nos planetas vs SolarFire

### Aspect Engine (`core/aspect_engine.py`)
- Recebe: lista de objetos astrológicos `{id, type, longitude, speed}`
- Detecta: aspectos entre quaisquer dois objetos
- Expõe por aspecto: id único, ângulo exato, orbe, phase (applying/separating/exact), precisão geométrica (0–100), harmônico
- Configuração de aspectos e orbes: `config/aspects.yaml` — externo ao código
- **Não conhece "planetas"** — trabalha com "objetos astrológicos" genéricos

---

## O que o Core NÃO faz

- ❌ Não interpreta aspectos
- ❌ Não atribui pesos temáticos (AstroHair, AstroDiet, etc.)
- ❌ Não gera texto, recomendações ou PDFs
- ❌ Não acessa banco de dados
- ❌ Não conhece os produtos Kalon
- ❌ Não tem estado — cada chamada é independente

---

## Interfaces públicas

```python
from core.astro_engine import calculate_chart
chart = calculate_chart(year, month, day, hour, minute, latitude, longitude, timezone_offset)

from core.aspect_engine import detect_aspects, objects_from_chart
objects = objects_from_chart(chart)
aspects = detect_aspects(objects)
```

---

## Schema de saída

### Planeta
```json
{
  "longitude": 155.507355,
  "signo": "Virgem",
  "grau": 5, "minuto": 30, "segundo": 25,
  "formatado": "5°30'25'' Virgem",
  "retrogrado": false,
  "speed_longitude": 0.966741
}
```

### Aspecto
```json
{
  "id": "SUN_TRI_MAR",
  "object1_id": "SUN", "object1_type": "planet",
  "object2_id": "MAR", "object2_type": "planet",
  "tipo": "Trígono",
  "aspect_angle": 120, "actual_angle": 119.74,
  "orbe": 0.26, "phase": "applying",
  "precisao": 97, "harmonico": true, "active": true
}
```

---

## Regra de extensão

O Core pode ser estendido apenas quando:
1. A extensão é matematicamente necessária
2. Todos os testes existentes continuam passando
3. `BASELINE_SOLARFIRE.json` é re-validado
4. O Astro Doctor retorna 100% OK
5. Uma nova tag Git é criada (`core-v1.1`, etc.)

**Nenhuma lógica de negócio, produto ou interpretação entra no Core.**

---

## Arquitetura de motores
Core v1.0 (frozen)

├── Astro Engine

└── Aspect Engine
Query Engine (Fase 3)

Timeline Engine (Fase 4)

Rule Engine (Fase 5)

└── AstroHair · AstroDiet · AstroCash · AstroLove

---

## Diagnóstico

```bash
python tools/astro_doctor.py
python tests/test_core.py
```

*Este documento não deve ser editado exceto em versões maiores do Core (v2.0+).*
