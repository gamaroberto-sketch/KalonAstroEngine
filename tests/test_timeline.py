import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timeline.timeline_engine import generate

def test_timeline():
    print("--- Teste 1: Lua percorrendo 7 dias ---")
    start = datetime(2026, 7, 1, 0, 0)
    end = datetime(2026, 7, 7, 0, 0)

    events = list(generate(start, end, step="1d"))

    # Validar:
    assert len(events) == 7
    assert all("datetime" in e for e in events)
    assert all("planets" in e for e in events)
    assert all("aspects" in e for e in events)
    assert all("MOON" in e["planets"] for e in events)

    # Mostrar posição da Lua em cada dia
    for e in events:
        moon = e["planets"]["MOON"]
        print(f"{e['datetime']}  Lua: {moon['signo']:<12} {moon['longitude']:.2f}°  speed={moon['speed_longitude']:.2f}")

    print("\n--- Teste 2: Filtro por objetos (apenas Lua e Vênus) ---")
    events_filtered = list(generate(
        datetime(2026, 7, 1, 0, 0),
        datetime(2026, 7, 7, 0, 0),
        step="1d",
        filters={"objects": ["MOON", "VEN"]}
    ))

    # Validar que todos os aspectos envolvem MOON ou VEN
    for e in events_filtered:
        for asp in e["aspects"]:
            assert asp["object1_id"] in ["MOON","VEN"] or asp["object2_id"] in ["MOON","VEN"]

    print(f'Filtro MOON/VEN: {sum(len(e["aspects"]) for e in events_filtered)} aspectos em 7 dias')

    print("\n--- Teste 3: Filtro por phase exact ---")
    events_exact = list(generate(
        datetime(2026, 7, 1, 0, 0),
        datetime(2026, 7, 7, 0, 0),
        step="1d",
        filters={"phases": ["exact"]}
    ))

    exact_count = sum(len(e["aspects"]) for e in events_exact)
    print(f'Aspectos exact em 7 dias: {exact_count}')
    
    print("\n[OK] Todos os testes da Timeline rodaram com sucesso.")

if __name__ == "__main__":
    test_timeline()
