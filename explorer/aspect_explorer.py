"""
Kalon Astro Engine — Aspect Explorer (Fase 2B)
Ferramenta CLI interativa para exploração de aspectos astrológicos.
"""

import argparse
import json
import csv
import sys
import os

# Ajuste do path para importar os módulos core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.astro_engine import calculate_chart
from core.aspect_engine import detect_aspects, objects_from_chart


# Dicionário de fallback caso o aspect_engine use IDs ou nomes em inglês/português
NAMES = {
    "SUN": "Sol", "MOON": "Lua", "MERCURY": "Mercúrio", "VENUS": "Vênus", 
    "MARS": "Marte", "JUPITER": "Júpiter", "SATURN": "Saturno", "URANUS": "Urano", 
    "NEPTUNE": "Netuno", "PLUTO": "Plutão",
    "ASC": "Ascendente", "MC": "Meio do Céu",
    # Fallback para caso os IDs já venham em PT-BR
    "Sol": "Sol", "Lua": "Lua", "Mercúrio": "Mercúrio", "Vênus": "Vênus",
    "Marte": "Marte", "Júpiter": "Júpiter", "Saturno": "Saturno",
    "Urano": "Urano", "Netuno": "Netuno", "Plutão": "Plutão",
    "Ascendente": "Ascendente", "Meio do Céu": "Meio do Céu",
    "Casa 1": "Casa 1", "Casa 2": "Casa 2", "Casa 3": "Casa 3", "Casa 4": "Casa 4",
    "Casa 5": "Casa 5", "Casa 6": "Casa 6", "Casa 7": "Casa 7", "Casa 8": "Casa 8",
    "Casa 9": "Casa 9", "Casa 10": "Casa 10", "Casa 11": "Casa 11", "Casa 12": "Casa 12"
}

def translate_phase(phase):
    phase = phase.lower()
    if phase == 'applying': return 'Aplicando'
    if phase == 'separating': return 'Separando'
    if phase == 'exact': return 'Exato'
    return phase.capitalize()


def print_table(aspects):
    if not aspects:
        print("Nenhum aspecto encontrado com os filtros fornecidos.")
        return

    print(f"\n{'ID':<15} | {'Planetas':<25} | {'Tipo':<12} | {'Âng. Real':<10} | {'Orbe':<6} | {'Fase':<10} | {'Natureza':<10}")
    print("-" * 100)
    
    total_orb = 0.0
    harmonic_count = 0
    tense_count = 0
    
    for asp in aspects:
        p1 = NAMES.get(asp['object1_id'], asp['object1_id'])
        p2 = NAMES.get(asp['object2_id'], asp['object2_id'])
        p1_p2 = f"{p1} - {p2}"
        
        tipo = asp.get('tipo', 'Desconhecido')
        ang_real = f"{asp.get('actual_angle', 0):.2f}°"
        orbe = f"{asp.get('orbe', 0):.2f}°"
        
        fase = translate_phase(asp.get('phase', 'N/A'))
        
        # Mapeamento do booleano harmonico para String
        is_harmonic = asp.get('harmonico', False)
        natureza = "Harmônico" if is_harmonic else "Tenso"
        
        if is_harmonic:
            harmonic_count += 1
        else:
            tense_count += 1
            
        total_orb += asp.get('orbe', 0)
        
        print(f"{asp.get('id', '-'):<15} | {p1_p2:<25} | {tipo:<12} | {ang_real:<10} | {orbe:<6} | {fase:<10} | {natureza:<10}")

    print("-" * 100)
    print("\n[ RESUMO ]")
    print(f"Total de aspectos : {len(aspects)}")
    print(f"Harmônicos        : {harmonic_count}")
    print(f"Tensos            : {tense_count}")
    
    avg_precision = total_orb / len(aspects) if aspects else 0
    print(f"Orbe Média        : {avg_precision:.2f}° (Precisão)")


def export_json(aspects, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(aspects, f, ensure_ascii=False, indent=4)
    print(f"Exportado com sucesso para JSON: {filename}")


def export_csv(aspects, filename):
    if not aspects:
        print("Nenhum dado para exportar em CSV.")
        return
        
    keys = aspects[0].keys()
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(aspects)
    print(f"Exportado com sucesso para CSV: {filename}")


def main():
    parser = argparse.ArgumentParser(description="Kalon Astro Engine - Aspect Explorer")
    
    # Dados de entrada
    parser.add_argument("--name", type=str, help="Nome da pessoa", default="Anônimo")
    parser.add_argument("--date", type=str, required=True, help="Data de nascimento (YYYY-MM-DD)")
    parser.add_argument("--time", type=str, required=True, help="Hora de nascimento (HH:MM)")
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude")
    parser.add_argument("--tz", type=float, required=True, help="Timezone offset (ex: -3.0)")
    
    # Filtros
    parser.add_argument("--planet", type=str, help="Filtrar aspectos envolvendo este planeta (ex: Sol, Vênus)")
    parser.add_argument("--type", type=str, help="Filtrar por tipo de aspecto (ex: Trígono, Conjunção)")
    parser.add_argument("--orb", type=float, help="Orbe máximo permitido em graus")
    parser.add_argument("--phase", type=str, choices=['applying', 'separating', 'exact'], help="Fase do aspecto (applying, separating, exact)")
    parser.add_argument("--harmonic", action="store_true", help="Mostrar apenas aspectos harmônicos")
    parser.add_argument("--tense", action="store_true", help="Mostrar apenas aspectos tensos")
    
    # Exportação
    parser.add_argument("--json", type=str, help="Caminho para exportar os dados em JSON")
    parser.add_argument("--csv", type=str, help="Caminho para exportar os dados em CSV")
    
    args = parser.parse_args()
    
    # Parse data e hora
    try:
        year, month, day = map(int, args.date.split('-'))
        hour, minute = map(int, args.time.split(':'))
    except ValueError:
        print("Erro: Formato de data ou hora inválido. Use YYYY-MM-DD e HH:MM.")
        sys.exit(1)
        
    print(f"\nCalculando mapa e aspectos para: {args.name} ({args.date} {args.time})")
    
    # 1. Obter os dados planetários do Motor Base (Fase 1.5)
    chart = calculate_chart(
        year=year, month=month, day=day,
        hour=hour, minute=minute,
        latitude=args.lat, longitude=args.lon,
        timezone_offset=args.tz
    )
    
    # 2. Extrair objetos e detectar aspectos do Motor de Aspectos (Fase 2)
    objects = objects_from_chart(chart)
    all_aspects = detect_aspects(objects)
    
    # 3. Aplicar Filtros Interativos
    filtered = all_aspects
    
    if args.planet:
        planet_query = args.planet.lower()
        filtered = [a for a in filtered if planet_query in str(a.get('object1_id', '')).lower() or planet_query in str(a.get('object2_id', '')).lower()]
        
    if args.type:
        type_query = args.type.lower()
        filtered = [a for a in filtered if a.get('tipo', '').lower() == type_query]
        
    if args.orb is not None:
        filtered = [a for a in filtered if a.get('orbe', 999) <= args.orb]
        
    if args.phase:
        filtered = [a for a in filtered if a.get('phase', '').lower() == args.phase.lower()]
        
    if args.harmonic:
        filtered = [a for a in filtered if a.get('harmonico') is True]
        
    if args.tense:
        filtered = [a for a in filtered if a.get('harmonico') is False]
        
    # 4. Exibir Saída
    print_table(filtered)
    
    # 5. Exportar se solicitado
    if args.json:
        export_json(filtered, args.json)
    if args.csv:
        export_csv(filtered, args.csv)


if __name__ == "__main__":
    main()
