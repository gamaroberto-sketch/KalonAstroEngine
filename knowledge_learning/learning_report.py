"""
Kalon Astro Engine — LearningReportGenerator
Gera relatórios visuais das observações (para o Studio CLI).
"""

from knowledge_learning.learning_engine import LearningEngine

class LearningReportGenerator:
    def __init__(self, engine: LearningEngine):
        self._engine = engine
        
    def render_global_summary(self) -> None:
        stats = self._engine.get_statistics()
        obs = self._engine.get_all_observations()
        
        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║         Learning Engine — Resumo             ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        print(f"  Total de observações registradas: {stats['total_observations']}")
        if stats['total_observations'] == 0:
            print("  Nenhuma observacao encontrada no momento.")
            print()
            return
            
        print()
        print("  ━━ POR VALIDAÇÃO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for val, count in stats['by_validation'].items():
            print(f"  {val:<15} {count}")
            
        print()
        # Mostrando as ultimas 5 observacoes
        recent = sorted(obs, key=lambda x: x["id"], reverse=True)[:5]
        print("  ━━ ÚLTIMAS 5 OBSERVAÇÕES ━━━━━━━━━━━━━━━━━━━━━")
        for o in recent:
            print(f"  {o['id']} | {o['event_id']} | {o['date']} | {o['user_validation']}")
        print()

    def render_event_history(self, event_id: str) -> None:
        obs = self._engine.get_observations(event_id)
        
        print()
        print("  ╔══════════════════════════════════════════════╗")
        print(f"  ║ Histórico de Observações: {event_id:<18} ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        
        if not obs:
            print("  Nenhuma observação registrada para este evento.")
            print()
            return
            
        for o in sorted(obs, key=lambda x: x["id"]):
            print(f"  ━━ {o['id']} ({o['date']}) ━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  Validação:   {o['user_validation']}")
            print(f"  Evidência:   {', '.join(o.get('evidence', []))}")
            print(f"  Observação:  {o.get('observation', '')}")
            
            ref = o.get('reflection', {})
            if ref.get('confirmed'):
                print(f"  Confirmed:   {ref['confirmed']}")
            if ref.get('surprised'):
                print(f"  Surprised:   {ref['surprised']}")
            if ref.get('learned'):
                print(f"  Learned:     {ref['learned']}")
            print()
