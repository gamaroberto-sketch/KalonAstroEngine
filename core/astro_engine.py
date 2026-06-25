"""
Kalon Astro Engine — Core Astronômico
Motor de cálculo baseado no Swiss Ephemeris (pyswisseph).
Fase 1.5: DeltaT aplicado corretamente nos planetas (ET).
           Casas/ASC/MC calculados em UT (método correto).
"""

import swisseph as swe
from typing import Optional


PLANETS = {
    "Sol":      swe.SUN,
    "Lua":      swe.MOON,
    "Mercúrio": swe.MERCURY,
    "Vênus":    swe.VENUS,
    "Marte":    swe.MARS,
    "Júpiter":  swe.JUPITER,
    "Saturno":  swe.SATURN,
    "Urano":    swe.URANUS,
    "Netuno":   swe.NEPTUNE,
    "Plutão":   swe.PLUTO,
}

SIGNS = [
    "Áries", "Touro", "Gêmeos", "Câncer",
    "Leão", "Virgem", "Libra", "Escorpião",
    "Sagitário", "Capricórnio", "Aquário", "Peixes"
]


def degree_to_sign(degree: float) -> dict:
    degree = degree % 360
    sign_index = int(degree / 30)
    degree_in_sign = degree % 30
    deg = int(degree_in_sign)
    minutes = int((degree_in_sign - deg) * 60)
    seconds = int(((degree_in_sign - deg) * 60 - minutes) * 60)
    return {
        "longitude": round(degree, 6),
        "signo": SIGNS[sign_index],
        "grau": deg,
        "minuto": minutes,
        "segundo": seconds,
        "formatado": f"{deg}°{minutes:02d}'{seconds:02d}'' {SIGNS[sign_index]}"
    }


def calculate_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    latitude: float,
    longitude: float,
    timezone_offset: float = 0.0,
    house_system: bytes = b'P'
) -> dict:
    ut_hour = hour - timezone_offset + (minute / 60.0)
    jd_ut = swe.julday(year, month, day, ut_hour)
    delta_t = swe.deltat(jd_ut)
    jd_et = jd_ut + delta_t

    planets_result = {}
    for name, planet_id in PLANETS.items():
        pos, _ = swe.calc_ut(jd_et, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
        retrogrado = pos[3] < 0
        data = degree_to_sign(pos[0])
        data["retrogrado"] = retrogrado
        if retrogrado:
            data["formatado"] += " R"
        planets_result[name] = data

    houses, ascmc = swe.houses(jd_ut, latitude, longitude, house_system)
    ascendant = degree_to_sign(ascmc[0])
    mc = degree_to_sign(ascmc[1])

    houses_result = {}
    for i, cusp in enumerate(houses, start=1):
        houses_result[f"Casa {i}"] = degree_to_sign(cusp)

    return {
        "input": {
            "data": f"{year:04d}-{month:02d}-{day:02d}",
            "hora_local": f"{hour:02d}:{minute:02d}",
            "timezone_offset": timezone_offset,
            "latitude": latitude,
            "longitude": longitude,
            "sistema_casas": house_system.decode()
        },
        "meta": {
            "jd_ut": round(jd_ut, 6),
            "jd_et": round(jd_et, 6),
            "delta_t_segundos": round(delta_t * 86400, 2)
        },
        "planetas": planets_result,
        "ascendente": ascendant,
        "meio_do_ceu": mc,
        "casas": houses_result
    }
