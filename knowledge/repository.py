"""
Kalon Astro Engine — KnowledgeRepository
Orquestra estados e escrita da Knowledge Base.
É a ÚNICA classe com permissão de escrever nos arquivos YAML.
Regra absoluta: nunca deletar — apenas mudar de estado.
"""

import os
import yaml
import shutil
from datetime import datetime

from knowledge.loader import KnowledgeLoader
from knowledge.journal import KnowledgeJournal
from knowledge.validator import KnowledgeValidator, KnowledgeValidationError

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KB = os.path.join(_BASE, "knowledge_base")


def _kb_path(filename: str) -> str:
    return os.path.join(_KB, filename)


def _load_yaml(filename: str) -> dict:
    path = _kb_path(filename)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_yaml(filename: str, data: dict) -> None:
    path = _kb_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=120)


class KnowledgeRepositoryError(Exception):
    pass


class KnowledgeRepository:
    """
    Gerencia o ciclo de vida das entradas da Knowledge Base.
    Única classe autorizada a escrever nos arquivos YAML.
    """

    def __init__(self, base_path: str = None):
        self._loader = KnowledgeLoader()
        self._journal = KnowledgeJournal()
        self._validator = KnowledgeValidator()

    # ─── Helpers de escrita ───────────────────────────────

    def _add_to_file(self, filename: str, event_id: str, entry: dict) -> None:
        """Adiciona uma entrada ao arquivo. Nunca substitui o arquivo inteiro."""
        data = _load_yaml(filename)
        if "entries" not in data or data["entries"] is None:
            data["entries"] = {}
        data["entries"][event_id] = entry
        # Atualizar contadores no topo do arquivo se existirem
        if "total_entries" in data:
            data["total_entries"] = len(data["entries"])
        if "last_updated" in data:
            data["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        _save_yaml(filename, data)

    def _remove_from_file(self, filename: str, event_id: str) -> dict:
        """Remove uma entrada do arquivo e a retorna. Lança se não encontrada."""
        data = _load_yaml(filename)
        entries = data.get("entries") or {}
        if event_id not in entries:
            raise KnowledgeRepositoryError(
                f"event_id '{event_id}' não encontrado em {filename}"
            )
        entry = dict(entries.pop(event_id))
        if "total_entries" in data:
            data["total_entries"] = len(entries)
        if "last_updated" in data:
            data["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        data["entries"] = entries
        _save_yaml(filename, data)
        return entry

    # ─── API pública ──────────────────────────────────────

    def create_pending(self, entry: dict, reviewer: str, reason: str) -> str:
        """
        Cria uma nova entrada em estado 'pending'.
        Valida o schema antes de persistir.
        Retorna o event_id.
        """
        event_id = entry.get("event_id")
        if not event_id:
            raise KnowledgeValidationError("entry deve conter 'event_id'")

        # Verificar se já existe em algum estado
        existing_state = self._loader.get_state(event_id)
        if existing_state:
            raise KnowledgeRepositoryError(
                f"'{event_id}' já existe no estado '{existing_state}'"
            )

        # Enriquecer com metadados de pending
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        entry = dict(entry)
        entry.setdefault("pending_reason", "incomplete")
        entry.setdefault("pending_since", now)
        entry.setdefault("reviewed", False)

        self._add_to_file("pending.yaml", event_id, entry)
        self._journal.log_created(event_id, reviewer, reason)
        return event_id

    def approve(self, event_id: str, reviewer: str, reason: str) -> None:
        """
        Transição: pending → approved (calibrated.yaml).
        Valida o schema completo antes de aprovar.
        """
        state = self._loader.get_state(event_id)
        if state != "pending":
            raise KnowledgeRepositoryError(
                f"'{event_id}' não está em 'pending' (estado atual: {state!r})"
            )

        entry = self._remove_from_file("pending.yaml", event_id)

        # Remover campos exclusivos do pending
        entry.pop("pending_reason", None)
        entry.pop("pending_since", None)
        entry.pop("notes", None)

        # Enriquecer com metadados de aprovação
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        entry["reviewed"] = True
        entry["reviewed_at"] = now
        entry["reviewed_by"] = reviewer

        # Validar schema completo
        self._validator.validate_entry(entry, context=event_id)

        # Adicionar a calibrated.yaml
        data = _load_yaml("calibrated.yaml")
        if "entries" not in data or data["entries"] is None:
            data["entries"] = {}
        data["entries"][event_id] = entry
        data["last_updated"] = now
        data["total_entries"] = len(data["entries"])
        _save_yaml("calibrated.yaml", data)

        self._journal.log_approved(event_id, reviewer, reason)

    def update(self, event_id: str, field: str, value,
               reviewer: str, reason: str) -> None:
        """
        Atualiza um campo de uma entrada em qualquer estado (approved ou pending).
        Loga from_value e to_value no journal.
        """
        state = self._loader.get_state(event_id)
        if state not in ("approved", "pending"):
            raise KnowledgeRepositoryError(
                f"'{event_id}' não está em estado editável (estado atual: {state!r})"
            )

        filename = "calibrated.yaml" if state == "approved" else "pending.yaml"
        data = _load_yaml(filename)
        entries = data.get("entries") or {}

        if event_id not in entries:
            raise KnowledgeRepositoryError(
                f"'{event_id}' não encontrado em {filename}"
            )

        from_value = entries[event_id].get(field)
        entries[event_id][field] = value
        data["entries"] = entries
        if "last_updated" in data:
            data["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        _save_yaml(filename, data)

        self._journal.log_updated(event_id, field, from_value, value, reviewer, reason)

    def reject(self, event_id: str, reviewer: str, reason: str) -> None:
        """
        Transição: pending → rejected (rejected.yaml).
        """
        state = self._loader.get_state(event_id)
        if state != "pending":
            raise KnowledgeRepositoryError(
                f"'{event_id}' não está em 'pending' (estado atual: {state!r})"
            )

        entry = self._remove_from_file("pending.yaml", event_id)

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        entry["rejected_at"] = now
        entry["rejected_by"] = reviewer
        entry["rejection_reason"] = reason
        entry["original_state"] = "pending"

        self._add_to_file("rejected.yaml", event_id, entry)
        self._journal.log_rejected(event_id, reviewer, reason)

    def restore(self, event_id: str, reviewer: str, reason: str) -> None:
        """
        Transição: rejected → pending (pending_reason: interrupted).
        """
        state = self._loader.get_state(event_id)
        if state != "rejected":
            raise KnowledgeRepositoryError(
                f"'{event_id}' não está em 'rejected' (estado atual: {state!r})"
            )

        entry = self._remove_from_file("rejected.yaml", event_id)

        # Limpar metadados de rejeição e marcar como interrompida
        entry.pop("rejected_at", None)
        entry.pop("rejected_by", None)
        entry.pop("rejection_reason", None)
        entry.pop("original_state", None)
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        entry["pending_reason"] = "interrupted"
        entry["pending_since"] = now
        entry["restored_by"] = reviewer
        entry["restored_at"] = now

        self._add_to_file("pending.yaml", event_id, entry)
        self._journal.log_restored(event_id, reviewer, reason)

    def archive(self, event_id: str, reviewer: str, reason: str) -> None:
        """
        Transição: approved → archived (archived.yaml).
        """
        state = self._loader.get_state(event_id)
        if state != "approved":
            raise KnowledgeRepositoryError(
                f"'{event_id}' não está em 'approved' (estado atual: {state!r})"
            )

        entry = self._remove_from_file("calibrated.yaml", event_id)

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        entry["archived_at"] = now
        entry["archived_by"] = reviewer
        entry["archive_reason"] = reason
        entry["original_state"] = "approved"

        self._add_to_file("archived.yaml", event_id, entry)
        self._journal.log_archived(event_id, reviewer, reason)

    def snapshot(self) -> str:
        """
        Gera um snapshot do calibrated.yaml em knowledge_base/snapshots/.
        Retorna o path do arquivo gerado.
        """
        snapshots_dir = os.path.join(_KB, "snapshots")
        os.makedirs(snapshots_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        dest = os.path.join(snapshots_dir, f"snapshot_{date_str}.yaml")
        shutil.copy2(_kb_path("calibrated.yaml"), dest)
        return dest
