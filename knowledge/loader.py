"""
Kalon Astro Engine — KnowledgeLoader
Leitura unificada de todos os arquivos da Knowledge Base.
Responsabilidade: SOMENTE LEITURA. Sem escrita. Sem lógica de negócio.
"""

import os
import yaml

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KB = os.path.join(_BASE, "knowledge_base")


def _yaml_path(filename: str) -> str:
    return os.path.join(_KB, filename)


def _load_file(filename: str, default) -> any:
    path = _yaml_path(filename)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data is not None else default


class KnowledgeLoader:
    """
    Leitura unificada dos 4 arquivos da Knowledge Base.
    Todos os métodos retornam dados frescos do disco (sem cache interno).
    """

    def load_approved(self) -> dict:
        """Retorna entries do calibrated.yaml."""
        data = _load_file("calibrated.yaml", {"entries": {}})
        return data.get("entries", {}) or {}

    def load_pending(self) -> dict:
        """Retorna entries do pending.yaml."""
        data = _load_file("pending.yaml", {"entries": {}})
        return data.get("entries", {}) or {}

    def load_rejected(self) -> dict:
        """Retorna entries do rejected.yaml."""
        data = _load_file("rejected.yaml", {"entries": {}})
        return data.get("entries", {}) or {}

    def load_archived(self) -> dict:
        """Retorna entries do archived.yaml."""
        data = _load_file("archived.yaml", {"entries": {}})
        return data.get("entries", {}) or {}

    def load_journal(self) -> list:
        """Retorna lista de registros do journal.yaml."""
        data = _load_file("journal.yaml", {"entries": []})
        return data.get("entries", []) or []

    def load_all(self) -> dict:
        """Retorna dict com todos os estados."""
        return {
            "approved": self.load_approved(),
            "pending":  self.load_pending(),
            "rejected": self.load_rejected(),
            "archived": self.load_archived(),
        }

    def get_by_id(self, event_id: str) -> dict | None:
        """
        Busca um event_id em todos os arquivos.
        Retorna (entry, state) ou (None, None) se não encontrado.
        """
        for state, entries in self.load_all().items():
            if event_id in entries:
                entry = dict(entries[event_id])
                entry["_state"] = state
                return entry
        return None

    def get_state(self, event_id: str) -> str | None:
        """Retorna o estado atual: 'approved'|'pending'|'rejected'|'archived'|None."""
        for state, entries in self.load_all().items():
            if event_id in entries:
                return state
        return None

    def get_all_event_ids(self) -> set:
        """Retorna set de todos os event_ids em qualquer estado."""
        ids = set()
        for entries in self.load_all().values():
            ids.update(entries.keys())
        return ids
