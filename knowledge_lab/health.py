"""
Kalon Astro Engine — KnowledgeHealthAnalyzer
Calcula o Health Score global da Knowledge Base considerando
cobertura, consistência e confiança.
"""

from knowledge.loader import KnowledgeLoader
from knowledge_lab.coverage import CoverageAnalyzer
from knowledge_lab.conflicts import ConflictDetector
import statistics

def _make_bar(pct: float, width: int = 20) -> str:
    filled = int((pct / 100) * width)
    return "█" * filled + "░" * (width - filled)


class KnowledgeHealthAnalyzer:
    def __init__(self, loader: KnowledgeLoader):
        self._loader = loader
        self._coverage = CoverageAnalyzer(loader)
        self._conflicts = ConflictDetector(loader)

    def get_coverage_score(self) -> dict:
        rep = self._coverage.get_coverage_report()
        return {
            "calibrated": rep["calibrated"],
            "possible":   rep["total_possible"],
            "pct":        rep["pct"],
            "score":      int(rep["pct"])
        }

    def get_conflict_score(self) -> dict:
        rep = self._conflicts.get_all_conflicts()
        total_conflicts = rep["total"]
        # Penalidade: 10 pontos por conflito, mínimo 0
        score = max(0, 100 - (total_conflicts * 10))
        return {
            "conflicts": total_conflicts,
            "score":     score
        }

    def get_confidence_distribution(self) -> dict:
        entries = self._loader.load_approved()
        if not entries:
            return {
                "mean": 0, "min": 0, "max": 0, "std": 0,
                "buckets": {
                    ">=0.95": {"count": 0, "pct": 0},
                    "0.90-0.95": {"count": 0, "pct": 0},
                    "0.85-0.90": {"count": 0, "pct": 0},
                    "0.80-0.85": {"count": 0, "pct": 0},
                    "<0.80": {"count": 0, "pct": 0}
                },
                "below_080": 0, "below_085": 0, "above_090": 0
            }

        confidences = [float(e.get("confidence", 0.0)) for e in entries.values()]
        total = len(confidences)

        counts = {">=0.95": 0, "0.90-0.95": 0, "0.85-0.90": 0, "0.80-0.85": 0, "<0.80": 0}
        below_080 = 0
        below_085 = 0
        above_090 = 0

        for c in confidences:
            if c >= 0.95:
                counts[">=0.95"] += 1
                above_090 += 1
            elif c >= 0.90:
                counts["0.90-0.95"] += 1
                above_090 += 1
            elif c >= 0.85:
                counts["0.85-0.90"] += 1
            elif c >= 0.80:
                counts["0.80-0.85"] += 1
                below_085 += 1
            else:
                counts["<0.80"] += 1
                below_080 += 1
                below_085 += 1

        buckets = {}
        for k, v in counts.items():
            buckets[k] = {"count": v, "pct": round(v / total * 100, 1) if total else 0}

        return {
            "mean": round(statistics.mean(confidences), 3),
            "min": round(min(confidences), 3),
            "max": round(max(confidences), 3),
            "std": round(statistics.stdev(confidences) if total > 1 else 0.0, 3),
            "buckets": buckets,
            "below_080": below_080,
            "below_085": below_085,
            "above_090": above_090
        }

    def get_confidence_score(self) -> int:
        dist = self.get_confidence_distribution()
        base = dist["mean"] * 100
        penalidade = dist["below_080"] * 8 + dist["below_085"] * 1
        return max(0, min(100, int(base - penalidade)))

    def get_health_score(self) -> int:
        cov = self.get_coverage_score()["score"]
        conf = self.get_conflict_score()["score"]
        confi = self.get_confidence_score()

        # Média ponderada
        score = (cov * 0.30) + (conf * 0.30) + (confi * 0.40)
        return int(round(score))

    def get_entries_to_review(self) -> list:
        """Entradas com confidence < 0.85, ordenadas crescente."""
        entries = self._loader.load_approved()
        to_review = []
        for eid, entry in entries.items():
            conf = float(entry.get("confidence", 0.0))
            if conf < 0.85:
                to_review.append({
                    "event_id": eid,
                    "confidence": conf,
                    "polarity": entry.get("polarity", "?"),
                    "motivo": "revisar calibração"
                })
        return sorted(to_review, key=lambda x: x["confidence"])

    def render(self) -> None:
        cov_info = self.get_coverage_score()
        conf_info = self.get_conflict_score()
        dist = self.get_confidence_distribution()
        confi_score = self.get_confidence_score()
        health_score = self.get_health_score()
        to_review = self.get_entries_to_review()

        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║      Kalon Knowledge Health Report       ║")
        print("  ╚══════════════════════════════════════════╝")
        print()
        
        # Cobertura
        print(f"  Cobertura        {cov_info['pct']}%  {_make_bar(cov_info['pct'])}")
        
        # Conflitos (0 conflitos = 100% bar)
        conflict_pct = 100.0 if conf_info['conflicts'] == 0 else 0.0
        print(f"  Conflitos        {conf_info['conflicts']:<5} {_make_bar(conflict_pct)}")
        
        # Conf. média
        mean_pct = dist['mean'] * 100
        print(f"  Conf. media      {dist['mean']:<5} {_make_bar(mean_pct)}")
        print()
        
        print("  Distribuicao de Confianca")
        for bucket, data in dist["buckets"].items():
            bar = _make_bar(data["pct"], width=10)
            print(f"  {bucket:<9} {bar}  {data['count']} entradas")
        print()
        
        if to_review:
            print(f"  Entradas para revisao (conf < 0.85):")
            for r in to_review:
                print(f"    {r['event_id']:<14} {r['confidence']:.2f}  {r['motivo']}")
        else:
            print("  Nenhuma entrada requer revisao imediata (todas >= 0.85).")
            
        print()
        
        if health_score >= 90:
            emoji, label = "🟢", "EXCELENTE"
        elif health_score >= 75:
            emoji, label = "🟡", "BOM"
        elif health_score >= 60:
            emoji, label = "🟠", "REGULAR"
        else:
            emoji, label = "🔴", "ATENÇÃO"

        print("  ══════════════════════════════════════════")
        print(f"  Knowledge Health Score:  {health_score}/100  {emoji} {label}")
        print("  ══════════════════════════════════════════")
        print()
