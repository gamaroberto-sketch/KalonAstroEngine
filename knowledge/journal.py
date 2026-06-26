"""
Kalon Astro Engine — KnowledgeJournal
Escrita append-only no journal.yaml.
Responsabilidade: NUNCA LER para lógica de negócio. NUNCA DELETAR entradas.
"""

import os
import yaml
from datetime import datetime

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JOURNAL_PATH = os.path.join(_BASE, "knowledge_base", "journal.yaml")


class KnowledgeJournal:
    """
    Registro append-only de todas as operações na Knowledge Base.
    Cada operação no KnowledgeRepository gera exatamente um registro aqui.
    """

    def __init__(self, journal_path: str = None):
        self._path = journal_path or _JOURNAL_PATH

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def _append(self, record: dict) -> None:
        """Persiste um registro no journal. NUNCA sobrescreve."""
        # Ler estado atual
        if os.path.exists(self._path):
            with open(self._path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {"entries": []}
        else:
            data = {"entries": []}

        entries = data.get("entries") or []
        entries.append(record)
        data["entries"] = entries

        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                      sort_keys=False, width=120)

    def _record(self, action: str, event_id: str, previous_state, new_state: str,
                reviewer: str, reason: str,
                field=None, from_value=None, to_value=None,
                notes=None, timestamp: str = None) -> dict:
        return {
            "timestamp":      timestamp or self._now(),
            "action":         action,
            "event_id":       event_id,
            "previous_state": previous_state,
            "new_state":      new_state,
            "reviewer":       reviewer,
            "field":          field,
            "from_value":     from_value,
            "to_value":       to_value,
            "reason":         reason,
            "notes":          notes,
        }

    # ─── API pública ──────────────────────────────────────

    def log_created(self, event_id: str, reviewer: str, reason: str,
                    notes: str = None, timestamp: str = None) -> None:
        self._append(self._record(
            "created", event_id, None, "pending",
            reviewer, reason, notes=notes, timestamp=timestamp
        ))

    def log_approved(self, event_id: str, reviewer: str, reason: str,
                     notes: str = None, timestamp: str = None) -> None:
        self._append(self._record(
            "approved", event_id, "pending", "approved",
            reviewer, reason, notes=notes, timestamp=timestamp
        ))

    def log_updated(self, event_id: str, field: str, from_value, to_value,
                    reviewer: str, reason: str, timestamp: str = None) -> None:
        # O estado não muda em updates; usamos None como sentinel
        self._append(self._record(
            "updated", event_id, None, None,
            reviewer, reason,
            field=field, from_value=from_value, to_value=to_value,
            timestamp=timestamp
        ))

    def log_rejected(self, event_id: str, reviewer: str, reason: str,
                     notes: str = None, timestamp: str = None) -> None:
        self._append(self._record(
            "rejected", event_id, "pending", "rejected",
            reviewer, reason, notes=notes, timestamp=timestamp
        ))

    def log_restored(self, event_id: str, reviewer: str, reason: str,
                     notes: str = None, timestamp: str = None) -> None:
        self._append(self._record(
            "restored", event_id, "rejected", "pending",
            reviewer, reason, notes=notes, timestamp=timestamp
        ))

    def log_archived(self, event_id: str, reviewer: str, reason: str,
                     notes: str = None, timestamp: str = None) -> None:
        self._append(self._record(
            "archived", event_id, "approved", "archived",
            reviewer, reason, notes=notes, timestamp=timestamp
        ))

    def log_deferred(self, event_id: str, reviewer: str, reason: str,
                     notes: str = None, timestamp: str = None) -> None:
        self._append(self._record(
            "deferred", event_id, "pending", "pending",
            reviewer, reason, notes=notes, timestamp=timestamp
        ))

    def get_history(self, event_id: str) -> list:
        """Retorna todos os registros do journal para um event_id específico."""
        if not os.path.exists(self._path):
            return []
        with open(self._path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {"entries": []}
        entries = data.get("entries") or []
        return [r for r in entries if r.get("event_id") == event_id]
