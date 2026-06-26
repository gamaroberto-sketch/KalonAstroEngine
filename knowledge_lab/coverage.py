"""
Kalon Astro Engine — CoverageAnalyzer
Calcula a cobertura da Knowledge Base em relação ao universo de eventos possíveis.
Universo: aspectos maiores (CON/OPP/TRI/SQR/SEX) × 10 planetas = 50 eventos.
Calculado dinamicamente a partir de config/aspects.yaml.
"""

import os
import yaml

from knowledge.loader import KnowledgeLoader

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ASPECTS_YAML = os.path.join(_BASE, "config", "aspects.yaml")

# Mapeamento de nomes do aspects.yaml para abreviações da KB
_ASPECT_TO_ABBR = {
    "Conjunção":  "CON",
    "Oposição":   "OPP",
    "Trígono":    "TRI",
    "Quadratura": "SQR",
    "Sextil":     "SEX",
}

# Planetas cobertos pelo AstroHair v0.1
_PLANETS = ["SUN", "MOO", "MER", "VEN", "MAR", "JUP", "SAT", "URA", "NEP", "PLU"]


def _make_bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


class CoverageAnalyzer:
    """
    Analisa a cobertura da KB em relação ao universo de eventos esperados.
    Calcula dinamicamente a partir do aspects.yaml — não hardcoded.
    """

    def __init__(self, loader: KnowledgeLoader):
        self._loader = loader

    def _load_supported_abbrs(self) -> list:
        """Carrega os aspectos suportados do aspects.yaml e retorna suas abreviações."""
        with open(_ASPECTS_YAML, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        abbrs = []
        for name in data.get("aspects", {}).keys():
            if name in _ASPECT_TO_ABBR:
                abbrs.append(_ASPECT_TO_ABBR[name])
        return abbrs

    def get_possible_events(self) -> set:
        """
        Retorna o universo completo de event_ids possíveis.
        Calculado dinamicamente: abbr × planeta = MOO_{ABBR}_{PLANET}
        """
        abbrs = self._load_supported_abbrs()
        events = set()
        for abbr in abbrs:
            for planet in _PLANETS:
                events.add(f"MOO_{abbr}_{planet}")
        return events

    def get_calibrated_events(self) -> set:
        """Retorna os event_ids atualmente aprovados na KB."""
        return set(self._loader.load_approved().keys())

    def get_missing_events(self) -> set:
        """Retorna eventos possíveis ainda sem entrada aprovada."""
        return self.get_possible_events() - self.get_calibrated_events()

    def get_coverage_report(self) -> dict:
        possible = self.get_possible_events()
        calibrated = self.get_calibrated_events()
        missing = sorted(possible - calibrated)
        total = len(possible)
        n_cal = len(calibrated)
        pct = round(n_cal / total * 100, 1) if total else 0.0
        return {
            "total_possible": total,
            "calibrated":     n_cal,
            "missing":        len(missing),
            "pct":            pct,
            "missing_events": missing,
        }

    def render(self) -> None:
        r = self.get_coverage_report()
        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║         Cobertura da Knowledge Base          ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        bar = _make_bar(r["pct"])
        print(f"  Calibradas: {r['calibrated']}/{r['total_possible']} ({r['pct']}%)")
        print(f"  [{bar}]")
        print()
        if r["missing_events"]:
            print(f"  Faltando ({r['missing']} eventos):")
            # Agrupa por aspecto para leitura mais fácil
            by_asp = {}
            for eid in r["missing_events"]:
                parts = eid.split("_")
                asp = parts[1] if len(parts) >= 3 else "?"
                by_asp.setdefault(asp, []).append(eid)
            for asp in sorted(by_asp):
                ids = "  ".join(by_asp[asp])
                print(f"    {asp}: {ids}")
        else:
            print("  Cobertura completa! Todos os eventos estão calibrados.")
        print()
