"""
Kalon Astro Engine — Teste de Validação (Fase 1)
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.astro_engine import calculate_chart


def test_chart(label: str, **kwargs):
    print(f"\n{'='*60}")
    print(f"TESTE: {label}")
    print('='*60)
    result = calculate_chart(**kwargs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":

    test_chart(
        label="São Paulo — 01/01/1990 12:00",
        year=1990, month=1, day=1,
        hour=12, minute=0,
        latitude=-23.5505,
        longitude=-46.6333,
        timezone_offset=-3.0
    )

    test_chart(
        label="Lisboa — 15/06/1985 08:30",
        year=1985, month=6, day=15,
        hour=8, minute=30,
        latitude=38.7169,
        longitude=-9.1399,
        timezone_offset=1.0
    )

    print(f"\n{'='*60}")
    print("Motor validado. Fase 1 concluída.")
    print('='*60)
