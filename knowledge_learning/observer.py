"""
Kalon Astro Engine — Observer CLI
CLI própria para gerir o ciclo de feedback humano (Learning Engine).
"""

import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_learning.learning_engine import LearningEngine
from knowledge_learning.confidence_updater import ConfidenceUpdater
from knowledge_learning.learning_report import LearningReportGenerator
from knowledge.repository import KnowledgeRepository


def main():
    parser = argparse.ArgumentParser(description="Kalon Learning Engine — Observer CLI")
    subparsers = parser.add_subparsers(dest="command")

    # LOG
    log_p = subparsers.add_parser("log", help="Registrar uma nova observação")
    log_p.add_argument("--event", required=True, help="event_id")
    log_p.add_argument("--app", required=True, help="rating do Reference App")
    log_p.add_argument("--solarfire", required=True, help="rating do SolarFire")
    log_p.add_argument("--validation", required=True, choices=["confirmed", "partial", "diverged"], help="Sua validacao")
    log_p.add_argument("--confirmed", default=None, help="Reflexao: confirmed")
    log_p.add_argument("--surprised", default=None, help="Reflexao: surprised")
    log_p.add_argument("--learned", default=None, help="Reflexao: learned")
    log_p.add_argument("--observation", default="", help="Observacao pura")
    log_p.add_argument("--evidence", nargs="+", default=[], help="Fontes de evidencia (ex: SolarFire ReferenceApp)")

    # HISTORY
    hist_p = subparsers.add_parser("history", help="Ver histórico de um evento")
    hist_p.add_argument("--event", required=True, help="event_id")

    # READY
    subparsers.add_parser("ready", help="Ver eventos prontos para atualizacao")

    # PROPOSE
    subparsers.add_parser("propose", help="Propor atualizacoes de confidence")

    # UPDATE
    update_p = subparsers.add_parser("update", help="Aplicar atualizacoes aprovadas")
    update_p.add_argument("--reviewer", required=True, help="Nome do revisor")

    args = parser.parse_args()

    engine = LearningEngine()
    repo = KnowledgeRepository()
    updater = ConfidenceUpdater(engine, repo)

    if args.command == "log":
        obs = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "event_id": args.event,
            "registered_by": "Roberto Gama",
            "reference_app_rating": args.app,
            "solarfire_rating": args.solarfire,
            "user_validation": args.validation,
            "reflection": {
                "confirmed": args.confirmed,
                "surprised": args.surprised,
                "learned": args.learned
            },
            "observation": args.observation,
            "evidence": args.evidence,
            "notes": None
        }
        obs_id = engine.log_observation(obs)
        print(f"Observação registrada com sucesso: {obs_id}")

    elif args.command == "history":
        LearningReportGenerator(engine).render_event_history(args.event)

    elif args.command == "ready":
        rules = updater._get_rules()
        min_obs = rules.get("min_observations_to_update", 3)
        processed_up_to = updater._model.get("processed_up_to_obs_id", "OBS_000")
        
        ready = engine.get_ready_for_update(min_obs, after_id=processed_up_to)
        print(f"Eventos prontos para atualização (>= {min_obs} novas observações):")
        for r in ready:
            print(f" - {r}")
        if not ready:
            print(" Nenhum evento atingiu o mínimo de observações.")

    elif args.command == "propose":
        proposals = updater.propose_updates()
        print("Propostas de Atualização:")
        for p in proposals:
            sign = "+" if p["delta"] > 0 else ""
            print(f" - {p['event_id']}: {p['current_confidence']} -> {p['proposed_confidence']} "
                  f"({sign}{p['delta']}) baseado em {p['obs_count']} novas obs.")
        if not proposals:
            print(" Nenhuma atualização pendente.")

    elif args.command == "update":
        results = updater.apply_updates(args.reviewer)
        print(f"Atualizações aplicadas: {len(results)}")
        for r in results:
            print(f" ✓ {r['event_id']} agora tem confidence {r['proposed_confidence']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
