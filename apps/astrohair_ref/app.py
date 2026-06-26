"""
Kalon AstroHair — Reference App v0.1
Aplicação CLI de referência interna para verificar coerência da Knowledge Base.
NÃO é produto comercial.

Uso:
    python apps/astrohair_ref/app.py               # Hoje + 7 dias
    python apps/astrohair_ref/app.py --date 2026-07-15
    python apps/astrohair_ref/app.py --days 14
"""

import sys
import os
import yaml
import argparse
from datetime import datetime, timedelta
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.astro_engine import calculate_chart
from core.aspect_engine import detect_aspects

# ─── Constantes ──────────────────────────────────────────

NATAL = dict(
    year=1957, month=8, day=29,
    hour=0, minute=0,
    latitude=-(22 + 59/60),
    longitude=-(49 + 52/60),
    timezone_offset=-3.0
)

NAME_TO_ID = {
    "Sol": "SUN", "Lua": "MOON", "Mercúrio": "MER",
    "Vênus": "VEN", "Marte": "MAR", "Júpiter": "JUP",
    "Saturno": "SAT", "Urano": "URA", "Netuno": "NEP", "Plutão": "PLU"
}

ASPECT_ABBR = {
    "Conjunção":      "CON",
    "Oposição":       "OPP",
    "Trígono":        "TRI",
    "Quadratura":     "SQR",
    "Sextil":         "SEX",
    "Quincúncio":     "QCX",
    "Semissextil":    "SSX",
    "Semiquadrado":   "SSQ",
    "Sesquiquadrado": "SES",
    "Quintil":        "QNT",
    "Biquintil":      "BQT",
}

# Aspectos suportados pelo AstroHair v0.1
# Aspectos menores (SSX, SSQ, SES, etc.) aguardam calibração futura
SUPPORTED_ASPECTS = {"Conjunção", "Oposição", "Trígono", "Quadratura", "Sextil"}

# Tabela de score base: (polarity, intensity) -> pontos
SCORE_TABLE = {
    ("positive", "low"):    +12,
    ("positive", "medium"): +18,
    ("positive", "high"):   +25,
    ("mixed",    "low"):     -3,
    ("mixed",    "medium"):  +2,
    ("mixed",    "high"):    +5,
    ("negative", "low"):    -12,
    ("negative", "medium"): -18,
    ("negative", "high"):   -25,
}

_KB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "knowledge_base", "calibrated.yaml"
)

# ─── Loaders (cacheados) ─────────────────────────────────

_natal_cache = None
_kb_cache = None


def load_natal() -> dict:
    global _natal_cache
    if _natal_cache is None:
        _natal_cache = calculate_chart(**NATAL)
    return _natal_cache


def load_kb() -> dict:
    global _kb_cache
    if _kb_cache is None:
        with open(_KB_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _kb_cache = data.get("entries", {})
    return _kb_cache


# ─── Detecção de Trânsitos ───────────────────────────────

def detect_moon_transits(date: datetime) -> list:
    """
    Detecta aspectos da Lua transitante com os planetas natais de Roberto.
    Retorna lista de dicts com: asp (aspecto bruto), kb_key, kb_entry (ou None).
    """
    natal = load_natal()
    kb = load_kb()

    # Calcular posição da Lua transitante (lat/lon 0 = trânsito universal)
    transit_chart = calculate_chart(
        year=date.year, month=date.month, day=date.day,
        hour=date.hour, minute=date.minute,
        latitude=0.0, longitude=0.0, timezone_offset=0.0
    )

    moon_data = transit_chart["planetas"]["Lua"]
    transit_moon = {
        "id": "MOON",
        "name": "Lua_transit",
        "type": "transit",
        "longitude": moon_data["longitude"],
        "speed": moon_data.get("speed_longitude", 13.0)
    }

    # Planetas natais (speed=0 pois são fixos)
    natal_objects = []
    for pname, pid in NAME_TO_ID.items():
        if pname in natal["planetas"]:
            pdata = natal["planetas"][pname]
            natal_objects.append({
                "id": pid,
                "name": f"{pname}_natal",
                "type": "natal_planet",
                "longitude": pdata["longitude"],
                "speed": 0.0
            })

    # Detectar todos os aspectos e filtrar os que envolvem a Lua transitante
    all_aspects = detect_aspects([transit_moon] + natal_objects)
    moon_aspects = [
        a for a in all_aspects
        if (a["object1_id"] == "MOON" or a["object2_id"] == "MOON")
        and a["tipo"] in SUPPORTED_ASPECTS
    ]

    # Para cada aspecto, construir chave KB e buscar entry
    results = []
    for asp in moon_aspects:
        # Identificar o planeta natal (o outro lado do aspecto)
        planet_id = asp["object2_id"] if asp["object1_id"] == "MOON" else asp["object1_id"]
        tipo_abbr = ASPECT_ABBR.get(asp["tipo"])

        if tipo_abbr is None:
            continue  # Aspecto menor sem abreviação — pular

        kb_key = f"MOO_{tipo_abbr}_{planet_id}"
        kb_entry = kb.get(kb_key)  # None se não calibrado

        results.append({
            "asp": asp,
            "kb_key": kb_key,
            "kb_entry": kb_entry,
            "planet_id": planet_id,
        })

    # Ordenar: com entry primeiro, depois sem dados
    results.sort(key=lambda r: (r["kb_entry"] is None, r["asp"]["orbe"]))
    return results


# ─── Score ───────────────────────────────────────────────

def calculate_score(transit_results: list) -> dict:
    """Calcula Opportunity Score 0-100 e retorna metadados."""
    contributions = []
    confidences = []
    matched_entries = []

    for r in transit_results:
        entry = r["kb_entry"]
        if entry is None:
            continue

        polarity = entry.get("polarity", "mixed")
        intensity = entry.get("intensity", "medium")
        confidence = entry.get("confidence", 0.8)

        base = SCORE_TABLE.get((polarity, intensity), 0)
        contribution = base * confidence
        contributions.append(contribution)
        confidences.append(confidence)
        matched_entries.append(entry)

    raw = sum(contributions) if contributions else 0
    clamped = max(-150, min(150, raw))
    score = int((clamped + 150) / 300 * 100)
    avg_conf = round(mean(confidences), 2) if confidences else 0.0

    if score >= 70:
        emoji, label = "🟢", "EXCELENTE"
    elif score >= 45:
        emoji, label = "🟡", "NEUTRO"
    else:
        emoji, label = "🔴", "DESFAVORÁVEL"

    return {
        "score": score,
        "emoji": emoji,
        "label": label,
        "avg_confidence": avg_conf,
        "matched_entries": matched_entries,
        "raw": round(raw, 2),
    }


# ─── Recomendações ───────────────────────────────────────

def build_recommendations(matched_entries: list) -> dict:
    favoraveis = []
    evitar = []
    for entry in matched_entries:
        if entry.get("polarity") == "positive":
            favoraveis.extend(entry.get("favorable_for", []))
        elif entry.get("polarity") == "negative":
            evitar.extend(entry.get("contraindications", []))

    # Deduplica preservando ordem
    favoraveis = list(dict.fromkeys(favoraveis))[:5]
    evitar = list(dict.fromkeys(evitar))[:5]
    return {"favoraveis": favoraveis, "evitar": evitar}


# ─── Renderização ─────────────────────────────────────────

def make_bar(score: int, width: int = 10) -> str:
    filled = max(0, min(width, int(score / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def render_day_full(date: datetime, transit_results: list, score_data: dict, recs: dict):
    """Renderiza o bloco completo de um único dia."""
    date_str = date.strftime("%d/%m/%Y")
    s = score_data["score"]
    emoji = score_data["emoji"]
    label = score_data["label"]
    conf = score_data["avg_confidence"]

    print()
    print(f"  ━━━━ RESULTADO DO DIA ━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    print(f"  {emoji} {label:<15}  |  Score: {s}  |  Confiança: {conf}")
    print()
    print(f"  ━━━━ ASPECTOS ATIVOS ━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    for r in transit_results:
        asp = r["asp"]
        kb_key = r["kb_key"]
        entry = r["kb_entry"]
        orbe = asp["orbe"]

        if entry:
            polarity = entry.get("polarity", "?")
            intensity = entry.get("intensity", "?")
            base = SCORE_TABLE.get((polarity, intensity), 0)
            contribution = int(base * entry.get("confidence", 0.8))
            sign = "+" if contribution >= 0 else ""
            tipo_pt = asp["tipo"]
            planet_name = r["planet_id"]
            conf_e = entry.get("confidence", 0.0)
            print(f"  ✓ {kb_key:<18} {tipo_pt:<20} {sign}{contribution:>4}  [conf {conf_e:.2f}]  orbe {orbe:.2f}°")
        else:
            print(f"  ? {kb_key:<18} {asp['tipo']:<20}  [sem dados]   orbe {orbe:.2f}°")

    if recs["favoraveis"]:
        print()
        print(f"  ━━━━ RECOMENDAÇÕES ━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        for item in recs["favoraveis"]:
            print(f"  • {item}")

    if recs["evitar"]:
        print()
        print(f"  ━━━━ EVITAR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        for item in recs["evitar"]:
            print(f"  • {item}")


def render_calendar(days_data: list):
    """Renderiza o calendário de múltiplos dias."""
    print()
    print(f"  ━━━━ PRÓXIMOS {len(days_data)} DIAS ━━━━━━━━━━━━━━━━━━━━")
    print()
    for d in days_data:
        date_str = d["date"].strftime("%d/%m")
        score = d["score_data"]["score"]
        emoji = d["score_data"]["emoji"]
        bar = make_bar(score)
        print(f"  {date_str}  {emoji}  {score:>3}  {bar}")


# ─── Main ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Kalon AstroHair Reference App v0.1"
    )
    parser.add_argument("--date", "-d", help="Data inicial (YYYY-MM-DD). Padrão: hoje.")
    parser.add_argument("--days", "-n", type=int, default=7,
                        help="Número de dias a exibir. Padrão: 7.")
    args = parser.parse_args()

    if args.date:
        start = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        start = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║     Kalon AstroHair — Reference App v0.1     ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print(f"  Data inicial: {start.strftime('%d/%m/%Y')}")
    print(f"  Mapa natal: Roberto Gama — 29/08/1957 Ourinhos SP")

    days_data = []
    first_day = True

    for i in range(args.days):
        date = start + timedelta(days=i)
        transit_results = detect_moon_transits(date)
        score_data = calculate_score(transit_results)
        recs = build_recommendations(score_data["matched_entries"])

        days_data.append({
            "date": date,
            "transit_results": transit_results,
            "score_data": score_data,
            "recs": recs,
        })

        # Renderiza detalhe completo apenas para o primeiro dia
        if first_day:
            print(f"\n  Data consultada: {date.strftime('%d/%m/%Y')}")
            render_day_full(date, transit_results, score_data, recs)
            first_day = False

    render_calendar(days_data)
    print()


if __name__ == "__main__":
    main()
