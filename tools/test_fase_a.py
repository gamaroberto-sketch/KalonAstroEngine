import sys, os
sys.path.insert(0, '.')

from knowledge.loader import KnowledgeLoader
from knowledge.validator import KnowledgeValidator
from knowledge.journal import KnowledgeJournal

l = KnowledgeLoader()
v = KnowledgeValidator()
j = KnowledgeJournal()

approved = l.load_approved()
journal_entries = l.load_journal()

print(f"Aprovadas:  {len(approved)}")
print(f"Pendentes:  {len(l.load_pending())}")
print(f"Rejeitadas: {len(l.load_rejected())}")
print(f"Arquivadas: {len(l.load_archived())}")
print(f"Journal:    {len(journal_entries)} registros")

print(f"Estado MOO_TRI_VEN: {l.get_state('MOO_TRI_VEN')}")
print(f"Estado FOO_BAR:     {l.get_state('FOO_BAR')}")

errors = 0
for eid, entry in approved.items():
    try:
        v.validate_entry(entry, context=eid)
    except Exception as e:
        print(f"ERRO {eid}: {e}")
        errors += 1
print(f"Validacao: {len(approved)-errors}/{len(approved)} entradas validas")

hist = j.get_history("MOO_TRI_VEN")
print(f"Historico MOO_TRI_VEN: {len(hist)} registros")
if hist:
    print(f"  primeiro: {hist[0]['action']} @ {hist[0]['timestamp']}")
    print(f"  segundo:  {hist[1]['action']} @ {hist[1]['timestamp']}")
