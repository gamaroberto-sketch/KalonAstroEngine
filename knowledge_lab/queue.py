"""
Kalon Astro Engine — QueueManager
Gerencia a fila de calibração: entradas pendentes + eventos ainda não tocados.
"""

from knowledge.loader import KnowledgeLoader
from knowledge.validator import KnowledgeValidator
from knowledge_lab.coverage import CoverageAnalyzer


class QueueManager:
    """
    Consolida o que ainda precisa ser calibrado:
    - Pendentes: entradas iniciadas mas não aprovadas
    - Missing: eventos possíveis sem qualquer entrada na KB
    """

    def __init__(self, loader: KnowledgeLoader):
        self._loader = loader
        self._validator = KnowledgeValidator()
        self._coverage = CoverageAnalyzer(loader)

    def get_pending(self) -> list:
        """
        Retorna lista de entradas pendentes enriquecidas com is_complete.
        """
        pending = self._loader.load_pending()
        result = []
        for event_id, entry in pending.items():
            result.append({
                "event_id":      event_id,
                "pending_reason": entry.get("pending_reason", "unknown"),
                "pending_since":  entry.get("pending_since", "?"),
                "is_complete":    self._validator.is_complete(entry),
                "missing_fields": self._validator.get_missing_fields(entry),
            })
        return sorted(result, key=lambda x: x["pending_since"])

    def get_missing_from_kb(self) -> list:
        """
        Eventos possíveis sem entrada approved nem pending.
        São os eventos nunca tocados.
        """
        possible = self._coverage.get_possible_events()
        approved_ids = set(self._loader.load_approved().keys())
        pending_ids = set(self._loader.load_pending().keys())
        missing = possible - approved_ids - pending_ids
        return sorted(missing)

    def get_priority_queue(self) -> list:
        """
        Lista ordenada por prioridade para calibração:
        1. Pending incompletos (interrupted/incomplete) — prioridade mais alta
        2. Missing events — nunca tocados
        """
        queue = []
        priority = 1

        # Pendentes incompletos primeiro
        for p in self.get_pending():
            if not p["is_complete"]:
                queue.append({
                    "event_id": p["event_id"],
                    "reason":   f"pending ({p['pending_reason']})",
                    "priority": priority,
                })
                priority += 1

        # Missing events
        for eid in self.get_missing_from_kb():
            queue.append({
                "event_id": eid,
                "reason":   "nao calibrado",
                "priority": priority,
            })
            priority += 1

        return queue

    def render(self) -> None:
        pending = self.get_pending()
        missing = self.get_missing_from_kb()

        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║           Fila de Calibracao                 ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        print(f"  Pendentes: {len(pending)}  |  Missing: {len(missing)}")
        print()

        if pending:
            print("  ━━━━ PENDENTES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for p in pending:
                status = "completo" if p["is_complete"] else "incompleto"
                missing_f = ", ".join(p["missing_fields"]) if p["missing_fields"] else "—"
                print(f"  • {p['event_id']:<20} [{p['pending_reason']}]  {status}")
                if not p["is_complete"]:
                    print(f"    faltando: {missing_f}")
            print()

        if missing:
            print("  ━━━━ FALTANDO NA KB ━━━━━━━━━━━━━━━━━━━━━━━")
            # Agrupa por aspecto
            by_asp = {}
            for eid in missing:
                parts = eid.split("_")
                asp = parts[1] if len(parts) >= 3 else "?"
                by_asp.setdefault(asp, []).append(eid)
            for asp in sorted(by_asp):
                print(f"  {asp}:", end="  ")
                print("  ".join(by_asp[asp]))
            print()

        if not pending and not missing:
            print("  Fila vazia! KB completa e sem pendencias.")
            print()
