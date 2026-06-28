import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.astro_engine import calculate_chart
from core.aspect_engine import detect_aspects, objects_from_chart
from query.query_engine import QueryEngine

def test_queries():
    print("Calculando o mapa base (Roberto Gama)...")
    chart = calculate_chart(
        year=1957, month=8, day=29,
        hour=0, minute=0,
        latitude=-22.9833, longitude=-49.8667,
        timezone_offset=-3.0
    )
    objects = objects_from_chart(chart)
    aspects = detect_aspects(objects)

    qe = QueryEngine(chart, aspects)

    print("\n--- TESTANDO QUERIES ---")

    # 1. aspectos_de
    asp_ven = qe.execute("aspectos_de", planeta="Vênus")
    print(f"1. aspectos_de('Vênus'): {len(asp_ven)} aspectos encontrados.")

    # 2. existe_aspecto
    tem_conj = qe.execute("existe_aspecto", planeta1="Sol", planeta2="Marte", tipo="Conjunção")
    print(f"2. existe_aspecto('Sol', 'Marte', 'Conjunção'): {tem_conj}")

    # 3. aspectos_por_tipo
    trigonos = qe.execute("aspectos_por_tipo", tipo="Trígono")
    print(f"3. aspectos_por_tipo('Trígono'): {len(trigonos)} encontrados.")

    # 4. aspectos_por_orbe
    exatos = qe.execute("aspectos_por_orbe", max_orbe=1.0)
    print(f"4. aspectos_por_orbe(1.0): {len(exatos)} encontrados.")

    # 5. aspectos_harmonicos
    harmonicos = qe.execute("aspectos_harmonicos")
    print(f"5. aspectos_harmonicos(): {len(harmonicos)} encontrados.")

    # 6. aspectos_tensos
    tensos = qe.execute("aspectos_tensos")
    print(f"6. aspectos_tensos(): {len(tensos)} encontrados.")

    # 7. planeta_em_signo
    sol_signo = qe.execute("planeta_em_signo", planeta="Sol")
    print(f"7. planeta_em_signo('Sol'): {sol_signo.get('formatado')}")

    # 8. planetas_em_signo
    em_virgem = qe.execute("planetas_em_signo", signo="Virgem")
    print(f"8. planetas_em_signo('Virgem'): {em_virgem}")

    # 9. planeta_retrogrado
    mer_rx = qe.execute("planeta_retrogrado", planeta="Mercúrio")
    print(f"9. planeta_retrogrado('Mercúrio'): {mer_rx}")

    # 10. planetas_retrogrados
    retrogrados = qe.execute("planetas_retrogrados")
    print(f"10. planetas_retrogrados(): {retrogrados}")

    # 11. casa_do_planeta
    casa_sol = qe.execute("casa_do_planeta", planeta="Sol")
    print(f"11. casa_do_planeta('Sol'): {casa_sol}")

    # 12. planetas_na_casa
    pl_casa4 = qe.execute("planetas_na_casa", casa=4)
    print(f"12. planetas_na_casa(4): {pl_casa4}")

    # 13. aspectos_por_phase
    applying = qe.execute("aspectos_por_phase", phase="applying")
    print(f"13. aspectos_por_phase('applying'): {len(applying)} encontrados.")

    # 14. resumo_mapa
    resumo = qe.execute("resumo_mapa")
    print(f"14. resumo_mapa():\n{json.dumps(resumo, ensure_ascii=False, indent=2)}")

if __name__ == "__main__":
    test_queries()
    print("\n[OK] Todas as 14 queries rodaram com sucesso.")
