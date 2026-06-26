"""
Kalon Astro Engine — Simulator
Simula um dia específico usando a lógica do Reference App,
com output expandido para diagnóstico da KB.
"""

import sys
import os
from datetime import datetime
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.astro_engine import calculate_chart
from core.aspect_engine import detect_aspects
from knowledge.loader import KnowledgeLoader

# ─── Dados natais de Roberto Gama ────────────────────────
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
    "Conjunção": "CON", "Oposição": "OPP", "Trígono": "TRI",
    "Quadratura": "SQR", "Sextil": "SEX",
}

SUPPORTED_ASPECTS = set(ASPECT_ABBR.keys())

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

_natal_cache = None


def _load_natal():
    global _natal_cache
    if _natal_cache is None:
        _natal_cache = calculate_chart(**NATAL)
    return _natal_cache


class Simulator:
    """
    Simula um dia específico com output expandido para diagnóstico.
    Reutiliza a lógica central do Reference App mas expõe mais detalhes.
    """

    def __init__(self, loader: KnowledgeLoader):
        self._loader = loader

    def simulate_day(self, date: datetime) -> dict:
        natal = _load_natal()
        kb = self._loader.load_approved()

        # Calcular posição da Lua transitante
        transit_chart = calculate_chart(
            year=date.year, month=date.month, day=date.day,
            hour=12, minute=0,
            latitude=0.0, longitude=0.0, timezone_offset=0.0
        )
        moon_data = transit_chart["planetas"]["Lua"]
        transit_moon = {
            "id": "MOON", "name": "Lua_transit", "type": "transit",
            "longitude": moon_data["longitude"],
            "speed": moon_data.get("speed_longitude", 13.0)
        }

        # Planetas natais
        natal_objects = []
        for pname, pid in NAME_TO_ID.items():
            if pname in natal["planetas"]:
                pdata = natal["planetas"][pname]
                natal_objects.append({
                    "id": pid, "name": f"{pname}_natal",
                    "type": "natal_planet",
                    "longitude": pdata["longitude"],
                    "speed": 0.0
                })

        # Detectar aspectos e filtrar para suportados
        all_aspects = detect_aspects([transit_moon] + natal_objects)
        moon_aspects = [
            a for a in all_aspects
            if (a["object1_id"] == "MOON" or a["object2_id"] == "MOON")
            and a["tipo"] in SUPPORTED_ASPECTS
        ]

        # Enriquecer com KB
        aspects_data = []
        contributions = []
        confidences = []
        gaps = []
        matched_entries = []

        for asp in sorted(moon_aspects, key=lambda a: a["orbe"]):
            planet_id = asp["object2_id"] if asp["object1_id"] == "MOON" else asp["object1_id"]
            tipo_abbr = ASPECT_ABBR.get(asp["tipo"])
            if not tipo_abbr:
                continue
            kb_key = f"MOO_{tipo_abbr}_{planet_id}"
            entry = kb.get(kb_key)

            contribution = None
            if entry:
                polarity = entry.get("polarity", "mixed")
                intensity = entry.get("intensity", "medium")
                confidence = float(entry.get("confidence", 0.8))
                base = SCORE_TABLE.get((polarity, intensity), 0)
                contribution = round(base * confidence, 1)
                contributions.append(contribution)
                confidences.append(confidence)
                matched_entries.append(entry)
            else:
                gaps.append(kb_key)

            aspects_data.append({
                "kb_key":       kb_key,
                "tipo":         asp["tipo"],
                "orbe":         round(asp["orbe"], 2),
                "contribution": contribution,
                "kb_entry":     entry,
                "has_data":     entry is not None,
            })

        # Score
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

        # Recomendações
        favoraveis, evitar = [], []
        for entry in matched_entries:
            if entry.get("polarity") == "positive":
                favoraveis.extend(entry.get("favorable_for", []))
            elif entry.get("polarity") == "negative":
                evitar.extend(entry.get("contraindications", []))
        favoraveis = list(dict.fromkeys(favoraveis))[:5]
        evitar = list(dict.fromkeys(evitar))[:5]

        return {
            "date":           date,
            "moon_longitude": round(moon_data["longitude"], 2),
            "score":          score,
            "label":          label,
            "emoji":          emoji,
            "avg_confidence": avg_conf,
            "raw_score":      round(raw, 2),
            "aspects":        aspects_data,
            "recommendations": {"favoraveis": favoraveis, "evitar": evitar},
            "gaps":           gaps,
        }

    def render(self, date: datetime) -> None:
        d = self.simulate_day(date)

        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║       Knowledge Studio — Simulador           ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        print(f"  Data: {d['date'].strftime('%d/%m/%Y')}  |  Lua: {d['moon_longitude']}°")
        print()
        print(f"  {d['emoji']} {d['label']:<15}  Score: {d['score']}  "
              f"Raw: {d['raw_score']}  Conf: {d['avg_confidence']}")
        print()
        print("  ━━ ASPECTOS ATIVOS ━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for asp in d["aspects"]:
            if asp["has_data"]:
                sign = "+" if (asp["contribution"] or 0) >= 0 else ""
                print(f"  ✓ {asp['kb_key']:<20} {asp['tipo']:<14} "
                      f"{sign}{asp['contribution']:>5}  orbe {asp['orbe']:.2f}°")
            else:
                print(f"  ? {asp['kb_key']:<20} {asp['tipo']:<14} "
                      f"  [sem dados]   orbe {asp['orbe']:.2f}°")

        recs = d["recommendations"]
        if recs["favoraveis"]:
            print()
            print("  ━━ RECOMENDAÇÕES ━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for item in recs["favoraveis"]:
                print(f"  • {item}")

        if recs["evitar"]:
            print()
            print("  ━━ EVITAR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for item in recs["evitar"]:
                print(f"  • {item}")

        if d["gaps"]:
            print()
            print(f"  ━━ GAPS NA KB ({len(d['gaps'])} eventos sem dados) ━━━━━━━━━")
            for gap in d["gaps"]:
                print(f"  ○ {gap}")
        print()
