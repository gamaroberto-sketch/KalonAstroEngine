"""
Kalon Astro Engine — Knowledge Studio v1.0 — CLI Principal

Uso:
    python knowledge_lab/studio.py coverage
    python knowledge_lab/studio.py queue
    python knowledge_lab/studio.py rules
    python knowledge_lab/studio.py conflicts
    python knowledge_lab/studio.py confidence
    python knowledge_lab/studio.py simulate --date 2026-06-27
    python knowledge_lab/studio.py snapshot
"""

import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.loader import KnowledgeLoader
from knowledge.repository import KnowledgeRepository
from knowledge_lab.coverage import CoverageAnalyzer
from knowledge_lab.queue import QueueManager
from knowledge_lab.rule_coverage import RuleCoverageAnalyzer
from knowledge_lab.conflicts import ConflictDetector
from knowledge_lab.confidence import ConfidenceAnalyzer
from knowledge_lab.simulator import Simulator


def _header():
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║      Kalon Knowledge Studio v1.0             ║")
    print("  ╚══════════════════════════════════════════════╝")


def main():
    parser = argparse.ArgumentParser(
        prog="studio",
        description="Kalon Knowledge Studio v1.0 — Gestao da Knowledge Base"
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMANDO")

    subparsers.add_parser("coverage",   help="Cobertura da Knowledge Base (50 eventos possiveis)")
    subparsers.add_parser("queue",      help="Fila de calibracao: pendentes + missing")
    subparsers.add_parser("rules",      help="Distribuicao interna: polarity/intensity/rating/domain")
    subparsers.add_parser("conflicts",  help="Detectar inconsistencias semanticas")
    subparsers.add_parser("confidence", help="Estatisticas de confianca das entradas")

    sim_parser = subparsers.add_parser("simulate", help="Simular score de um dia especifico")
    sim_parser.add_argument("--date", "-d", default=None,
                            help="Data no formato YYYY-MM-DD (default: hoje)")

    subparsers.add_parser("snapshot", help="Gerar snapshot do calibrated.yaml")

    args = parser.parse_args()

    if not args.command:
        _header()
        print()
        parser.print_help()
        print()
        return

    loader = KnowledgeLoader()

    if args.command == "coverage":
        CoverageAnalyzer(loader).render()

    elif args.command == "queue":
        QueueManager(loader).render()

    elif args.command == "rules":
        RuleCoverageAnalyzer(loader).render()

    elif args.command == "conflicts":
        ConflictDetector(loader).render()

    elif args.command == "confidence":
        ConfidenceAnalyzer(loader).render()

    elif args.command == "simulate":
        if args.date:
            try:
                date = datetime.strptime(args.date, "%Y-%m-%d").replace(hour=12)
            except ValueError:
                print(f"  Erro: data invalida '{args.date}'. Use o formato YYYY-MM-DD.")
                sys.exit(1)
        else:
            date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        Simulator(loader).render(date)

    elif args.command == "snapshot":
        path = KnowledgeRepository().snapshot()
        print()
        print(f"  Snapshot gerado: {path}")
        print()


if __name__ == "__main__":
    main()
