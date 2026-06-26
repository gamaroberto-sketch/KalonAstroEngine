"""
Kalon Astro Engine — ConflictDetector
Detecta inconsistências semânticas nas entradas aprovadas da KB.

Regras de alerta:
  negative + contraindications=[]  → ALERTA (deveria ter algo a evitar)
  positive + favorable_for=[]      → ALERTA (deveria ter recomendações)
  positive + hair_day_rating=red   → ALERTA (mismatch semântico)
  negative + hair_day_rating=green → ALERTA (mismatch semântico)
"""

from knowledge.loader import KnowledgeLoader

# Ratings esperados por polarity (o que NÃO é esperado gera alerta)
_INVALID_RATING = {
    "positive": {"red"},
    "negative": {"green"},
    "mixed":    set(),   # mixed aceita qualquer rating
}


class ConflictDetector:
    """
    Detecta inconsistências semânticas nas entradas aprovadas da KB.
    Não modifica nenhum dado — apenas leitura e análise.
    """

    def __init__(self, loader: KnowledgeLoader):
        self._loader = loader

    def find_rating_polarity_mismatch(self) -> list:
        """
        Detecta entradas onde polarity e hair_day_rating são semanticamente inconsistentes.
        positive → red é mismatch.
        negative → green é mismatch.
        """
        entries = self._loader.load_approved()
        conflicts = []
        for event_id, entry in entries.items():
            polarity = entry.get("polarity", "")
            rating = entry.get("hair_day_rating", "")
            invalid = _INVALID_RATING.get(polarity, set())
            if rating in invalid:
                conflicts.append({
                    "event_id": event_id,
                    "polarity": polarity,
                    "rating":   rating,
                    "conflict": f"polarity='{polarity}' incompatível com hair_day_rating='{rating}'",
                })
        return sorted(conflicts, key=lambda x: x["event_id"])

    def find_low_confidence(self, threshold: float = 0.75) -> list:
        """
        Retorna entradas com confidence abaixo do threshold.
        Ordenadas pela menor confidence primeiro.
        """
        entries = self._loader.load_approved()
        low = []
        for event_id, entry in entries.items():
            conf = float(entry.get("confidence", 1.0))
            if conf < threshold:
                low.append({
                    "event_id":  event_id,
                    "confidence": conf,
                    "delta":     round(threshold - conf, 3),
                })
        return sorted(low, key=lambda x: x["confidence"])

    def find_empty_fields(self) -> list:
        """
        Detecta campos vazios semanticamente suspeitos:
          negative + contraindications=[]  → ALERTA
          positive + favorable_for=[]      → ALERTA
          mixed                            → OK (intencional)
        """
        entries = self._loader.load_approved()
        alerts = []
        for event_id, entry in entries.items():
            polarity = entry.get("polarity", "mixed")
            empty = []

            if polarity == "negative":
                if not entry.get("contraindications"):
                    empty.append("contraindications")

            elif polarity == "positive":
                if not entry.get("favorable_for"):
                    empty.append("favorable_for")

            # mixed → sem alerta por design

            if empty:
                alerts.append({
                    "event_id":    event_id,
                    "polarity":    polarity,
                    "empty_fields": empty,
                })
        return sorted(alerts, key=lambda x: x["event_id"])

    def get_all_conflicts(self) -> dict:
        mismatch = self.find_rating_polarity_mismatch()
        low_conf = self.find_low_confidence()
        empty    = self.find_empty_fields()
        return {
            "mismatch":       mismatch,
            "low_confidence": low_conf,
            "empty_fields":   empty,
            "total":          len(mismatch) + len(low_conf) + len(empty),
        }

    def render(self) -> None:
        conflicts = self.get_all_conflicts()

        print()
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║        Deteccao de Conflitos na KB           ║")
        print("  ╚══════════════════════════════════════════════╝")
        print()
        total = conflicts["total"]
        status = "Nenhum conflito encontrado." if total == 0 else f"{total} alertas encontrados."
        print(f"  {status}")
        print()

        if conflicts["mismatch"]:
            print("  ━━ MISMATCH POLARITY × RATING ━━━━━━━━━━━━━━━")
            for c in conflicts["mismatch"]:
                print(f"  ⚠  {c['event_id']:<20} {c['conflict']}")
            print()

        if conflicts["low_confidence"]:
            print("  ━━ BAIXA CONFIANCA (< 0.75) ━━━━━━━━━━━━━━━━━")
            for c in conflicts["low_confidence"]:
                print(f"  ⚠  {c['event_id']:<20} confidence={c['confidence']}  delta={c['delta']}")
            print()

        if conflicts["empty_fields"]:
            print("  ━━ CAMPOS VAZIOS SUSPEITOS ━━━━━━━━━━━━━━━━━━")
            for c in conflicts["empty_fields"]:
                fields = ", ".join(c["empty_fields"])
                print(f"  ⚠  {c['event_id']:<20} polarity={c['polarity']}  vazio: {fields}")
            print()

        if total == 0:
            print("  Tudo consistente! KB sem conflitos detectados.")
            print()
