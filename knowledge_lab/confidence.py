"""
Kalon Astro Engine — ConfidenceAnalyzer
Estatísticas de confiança das entradas aprovadas da KB.
"""

import statistics
from knowledge.loader import KnowledgeLoader


class ConfidenceAnalyzer:
    """
    Analisa os valores de confidence das entradas aprovadas.
    Útil para identificar entradas que precisam de recalibração.
    """

    def __init__(self, loader: KnowledgeLoader):
        self._loader = loader

    def _get_confidences(self) -> list:
        """Retorna lista de (event_id, confidence, polarity)."""
        entries = self._loader.load_approved()
        return [
            (eid, float(e.get("confidence", 0.0)), e.get("polarity", "?"))
            for eid, e in entries.items()
        ]

    def get_statistics(self) -> dict:
        data = self._get_confidences()
        if not data:
            return {"count": 0, "mean": 0, "min": 0, "max": 0, "std": 0, "median": 0}
        values = [d[1] for d in data]
        return {
            "count":  len(values),
            "mean":   round(statistics.mean(values), 3),
            "min":    round(min(values), 3),
            "max":    round(max(values), 3),
            "std":    round(statistics.stdev(values) if len(values) > 1 else 0.0, 3),
            "median": round(statistics.median(values), 3),
        }

    def get_by_polarity(self) -> dict:
        data = self._get_confidences()
        by_pol: dict = {}
        for _, conf, polarity in data:
            by_pol.setdefault(polarity, []).append(conf)
        result = {}
        for pol, vals in sorted(by_pol.items()):
            result[pol] = {
                "mean":  round(statistics.mean(vals), 3),
                "count": len(vals),
                "min":   round(min(vals), 3),
                "max":   round(max(vals), 3),
            }
        return result

    def get_below_threshold(self, threshold: float = 0.80) -> list:
        data = self._get_confidences()
        below = [
            {"event_id": eid, "confidence": conf, "polarity": pol}
            for eid, conf, pol in data if conf < threshold
        ]
        return sorted(below, key=lambda x: x["confidence"])

    def render(self) -> None:
        stats = self.get_statistics()
        by_pol = self.get_by_polarity()
        below = self.get_below_threshold(0.80)

        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║        Analise de Confianca da KB            ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        print(f"  Entradas: {stats['count']}")
        print(f"  Media:    {stats['mean']}  |  Mediana: {stats['median']}")
        print(f"  Min:      {stats['min']}   |  Max:     {stats['max']}   |  Std: {stats['std']}")
        print()

        print("  ━━ POR POLARIDADE ━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for pol, d in by_pol.items():
            print(f"  {pol:<12}  n={d['count']}  media={d['mean']}  [{d['min']} — {d['max']}]")
        print()

        if below:
            print(f"  ━━ ABAIXO DE 0.80 ({len(below)} entradas) ━━━━━━━━━━━━━━")
            for b in below:
                print(f"  ⚡ {b['event_id']:<22} {b['confidence']}  [{b['polarity']}]")
        else:
            print("  Todas as entradas acima de 0.80. Excelente!")
        print()
