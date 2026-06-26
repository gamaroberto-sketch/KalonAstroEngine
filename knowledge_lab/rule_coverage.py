"""
Kalon Astro Engine — RuleCoverageAnalyzer
Analisa as distribuições internas da Knowledge Base:
polaridade, intensidade, rating, domínios, tipo de aspecto.
"""

from collections import Counter
from knowledge.loader import KnowledgeLoader


def _bar(count: int, total: int, width: int = 15) -> str:
    filled = int(count / total * width) if total else 0
    return "█" * filled + "░" * (width - filled)


class RuleCoverageAnalyzer:
    """
    Analisa a distribuição interna das entradas aprovadas da KB.
    Útil para identificar vieses (ex: muitas entradas red, poucas green).
    """

    def __init__(self, loader: KnowledgeLoader):
        self._loader = loader

    def _get_approved(self) -> list:
        return list(self._loader.load_approved().values())

    def get_polarity_distribution(self) -> dict:
        entries = self._get_approved()
        c = Counter(e.get("polarity", "?") for e in entries)
        return dict(c)

    def get_intensity_distribution(self) -> dict:
        entries = self._get_approved()
        c = Counter(e.get("intensity", "?") for e in entries)
        return dict(c)

    def get_rating_distribution(self) -> dict:
        entries = self._get_approved()
        c = Counter(e.get("hair_day_rating", "?") for e in entries)
        return dict(c)

    def get_domain_distribution(self) -> dict:
        entries = self._get_approved()
        c = Counter()
        for e in entries:
            for domain in e.get("domains", []):
                c[domain] += 1
        return dict(c.most_common())

    def get_aspect_type_distribution(self) -> dict:
        """Extrai o tipo de aspecto do event_id (ex: MOO_TRI_VEN -> TRI)."""
        entries = self._get_approved()
        c = Counter()
        for e in entries:
            eid = e.get("event_id", "")
            parts = eid.split("_")
            if len(parts) >= 3:
                c[parts[1]] += 1
        return dict(c.most_common())

    def get_full_report(self) -> dict:
        return {
            "polarity":    self.get_polarity_distribution(),
            "intensity":   self.get_intensity_distribution(),
            "rating":      self.get_rating_distribution(),
            "domains":     self.get_domain_distribution(),
            "aspect_type": self.get_aspect_type_distribution(),
        }

    def render(self) -> None:
        report = self.get_full_report()
        total = sum(report["polarity"].values())

        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║       Distribuicao da Knowledge Base         ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        print(f"  Total de entradas aprovadas: {total}")
        print()

        def print_dist(title: str, data: dict):
            total_d = sum(data.values())
            print(f"  ━━ {title} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            for key, count in sorted(data.items(), key=lambda x: -x[1]):
                pct = count / total_d * 100 if total_d else 0
                bar = _bar(count, total_d)
                print(f"  {key:<12} {count:>3}  [{bar}] {pct:.0f}%")
            print()

        print_dist("POLARIDADE", report["polarity"])
        print_dist("INTENSIDADE", report["intensity"])
        print_dist("HAIR DAY RATING", report["rating"])
        print_dist("TIPO DE ASPECTO", report["aspect_type"])
        print_dist("DOMÍNIOS", report["domains"])
