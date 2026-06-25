"""
Kalon Astro Engine — Aspect Engine
Motor universal de detecção de aspectos astrológicos.

Fase 2A: objetos planeta × planeta
Fase 2B: + ASC, MC, IC, DSC (sem alterar algoritmo)
Fase 2C: + casas, nodos, Quíron, Lilith, pontos médios, asteroides

O engine não conhece 'planetas' — apenas 'objetos astrológicos'.
Qualquer objeto com {id, type, longitude} pode ser processado.
"""

import yaml
import os
from typing import Optional


_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "aspects.yaml"
)


def _load_aspects_config(config_path: Optional[str] = None) -> dict:
    path = config_path or _CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["aspects"]


def _angular_distance(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2) % 360
    if diff > 180:
        diff = 360 - diff
    return diff


def _determine_phase(lon1: float, lon2: float, speed1: float, speed2: float) -> str:
    relative_speed = speed1 - speed2
    diff = (lon1 - lon2) % 360
    if relative_speed == 0:
        return "exact"
    approaching = (diff > 180 and relative_speed > 0) or (diff <= 180 and relative_speed < 0)
    return "applying" if approaching else "separating"


def _calculate_precision(orb: float, max_orb: float) -> int:
    if max_orb == 0:
        return 100
    precision = max(0, 100 - int((orb / max_orb) * 100))
    return precision


def _build_aspect_id(id1: str, aspect_name: str, id2: str) -> str:
    abbreviations = {
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
    abbr = abbreviations.get(aspect_name, aspect_name[:3].upper())
    return f"{id1}_{abbr}_{id2}"


def detect_aspects(
    objects: list,
    config_path: Optional[str] = None,
    include_inactive: bool = False
) -> list:
    aspects_config = _load_aspects_config(config_path)
    results = []

    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            obj1 = objects[i]
            obj2 = objects[j]

            lon1 = obj1["longitude"]
            lon2 = obj2["longitude"]
            speed1 = obj1.get("speed", 1.0)
            speed2 = obj2.get("speed", 1.0)

            actual_angle = _angular_distance(lon1, lon2)

            for aspect_name, cfg in aspects_config.items():
                aspect_angle = cfg["angle"]
                max_orb = cfg["orb"]

                orb = abs(actual_angle - aspect_angle)
                active = orb <= max_orb

                if not active and not include_inactive:
                    continue

                phase = _determine_phase(lon1, lon2, speed1, speed2)
                if orb < 0.1:
                    phase = "exact"

                precision = _calculate_precision(orb, max_orb)
                aspect_id = _build_aspect_id(obj1["id"], aspect_name, obj2["id"])

                results.append({
                    "id": aspect_id,
                    "object1_id": obj1["id"],
                    "object1_type": obj1["type"],
                    "object2_id": obj2["id"],
                    "object2_type": obj2["type"],
                    "tipo": aspect_name,
                    "aspect_angle": aspect_angle,
                    "actual_angle": round(actual_angle, 6),
                    "orbe": round(orb, 6),
                    "phase": phase,
                    "precisao": precision,
                    "harmonico": cfg.get("harmonic", True),
                    "active": active
                })

    results.sort(key=lambda x: x["orbe"])
    return results


def objects_from_chart(chart: dict) -> list:
    objects = []
    planet_ids = {
        "Sol":      "SUN",
        "Lua":      "MOON",
        "Mercúrio": "MER",
        "Vênus":    "VEN",
        "Marte":    "MAR",
        "Júpiter":  "JUP",
        "Saturno":  "SAT",
        "Urano":    "URA",
        "Netuno":   "NEP",
        "Plutão":   "PLU",
    }
    for name, pid in planet_ids.items():
        if name in chart["planetas"]:
            p = chart["planetas"][name]
            objects.append({
                "id": pid,
                "name": name,
                "type": "planet",
                "longitude": p["longitude"],
                "speed": p.get("speed_longitude", p.get("speed", 1.0))
            })
    return objects
