"""
Script de migração retroativa do journal.
Gera entradas action:approved para as 35 entradas existentes no calibrated.yaml.
Executar UMA ÚNICA VEZ.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.loader import KnowledgeLoader
from knowledge.journal import KnowledgeJournal

loader = KnowledgeLoader()
journal = KnowledgeJournal()

approved = loader.load_approved()

# Determinar timestamp retroativo por review_date
def get_timestamp(entry: dict) -> str:
    review_date = entry.get("review_date") or entry.get("calibrated_at", "2026-06-25")
    date_str = str(review_date)[:10]
    return f"{date_str}T00:00:00"

print(f"\nMigracao retroativa do journal — {len(approved)} entradas\n")

for event_id, entry in sorted(approved.items()):
    ts = get_timestamp(entry)
    # log_created (pending) seguido de log_approved
    journal.log_created(
        event_id=event_id,
        reviewer="Roberto Gama",
        reason="Migracao retroativa — pre-journal (calibracao via SolarFire)",
        timestamp=ts
    )
    journal.log_approved(
        event_id=event_id,
        reviewer="Roberto Gama",
        reason="Migracao retroativa — aprovado via SolarFire calibration",
        timestamp=ts
    )
    print(f"  {ts}  {event_id}")

print(f"\n{len(approved)*2} registros gravados no journal.yaml")
print("Migracao concluida.")
