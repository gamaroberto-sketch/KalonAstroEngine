"""
Kalon Astro Engine — Timeline Engine
Fase 4: Motor de Linha do Tempo.

Percorre intervalos de tempo, calculando as posições e extraindo os aspectos
brutos do Astro Engine e Aspect Engine, formatados em um pacote otimizado
por instante. Sem interpretações, apenas geração determinística da linha do tempo.
"""

from typing import Optional, Generator
from datetime import datetime, timedelta
from core.astro_engine import calculate_chart
from core.aspect_engine import detect_aspects, objects_from_chart

def _parse_step(step_str: str) -> timedelta:
    step_str = step_str.strip().lower()
    if step_str.endswith('d'):
        return timedelta(days=float(step_str[:-1]))
    elif step_str.endswith('h'):
        return timedelta(hours=float(step_str[:-1]))
    elif step_str.endswith('m'):
        return timedelta(minutes=float(step_str[:-1]))
    else:
        return timedelta(days=1)  # Fallback seguro


def generate(
    start: datetime,
    end: datetime,
    step: str = "1d",
    filters: Optional[dict] = None
) -> Generator[dict, None, None]:
    """
    Percorre o tempo entre `start` e `end` e emite os dados planetários
    e os aspectos astrológicos isolados em cada momento de parada.
    """
    delta = _parse_step(step)
    current = start
    
    # Mapeamento do Core para gerar o schema compactado de planetas pelo ID
    name_to_id = {
        "Sol": "SUN", "Lua": "MOON", "Mercúrio": "MER", "Vênus": "VEN",
        "Marte": "MAR", "Júpiter": "JUP", "Saturno": "SAT", "Urano": "URA",
        "Netuno": "NEP", "Plutão": "PLU"
    }

    while current <= end:
        # 1. Calcula o motor base
        # Para trânsitos puros, usamos lat/lon 0.0 (casas não serão relevantes aqui)
        chart = calculate_chart(
            year=current.year, month=current.month, day=current.day,
            hour=current.hour, minute=current.minute,
            latitude=0.0, longitude=0.0, timezone_offset=0.0
        )
        
        objects = objects_from_chart(chart)
        aspects = detect_aspects(objects)
        
        # 2. Aplica Filtros de Otimização (se existirem)
        if filters:
            f_objects = filters.get("objects", [])
            f_types = filters.get("types", [])
            f_phases = filters.get("phases", [])
            
            filtered_aspects = []
            for asp in aspects:
                keep = True
                
                if f_objects:
                    if asp["object1_id"] not in f_objects and asp["object2_id"] not in f_objects:
                        keep = False
                        
                if keep and f_types:
                    if asp["tipo"] not in f_types:
                        keep = False
                        
                if keep and f_phases:
                    if asp["phase"] not in f_phases:
                        keep = False
                        
                if keep:
                    filtered_aspects.append(asp)
            aspects = filtered_aspects
            
        # 3. Empacota e formata as posições planetárias puras
        planets_out = {}
        for pname, pdata in chart.get("planetas", {}).items():
            pid = name_to_id.get(pname, pname)
            planets_out[pid] = {
                "longitude": pdata["longitude"],
                "signo": pdata["signo"],
                "speed_longitude": pdata.get("speed_longitude", 0.0)
            }
            
        # 4. Emite o yield do instante atual
        yield {
            "datetime": current.strftime("%Y-%m-%dT%H:%M:%S"),
            "planets": planets_out,
            "aspects": aspects
        }
        
        current += delta
