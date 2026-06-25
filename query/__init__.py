"""
Kalon Astro Engine — Query Engine (Fase 3)
Módulo de exportação de interface.
"""

from .query_engine import QueryEngine, QueryNotFoundError

__all__ = ["QueryEngine", "QueryNotFoundError"]
