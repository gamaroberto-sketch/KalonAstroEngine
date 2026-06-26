"""
Kalon Astro Engine — KnowledgeValidator
Validação de schema de entradas da Knowledge Base.
Responsabilidade: SOMENTE VALIDAÇÃO. Sem I/O.
"""


class KnowledgeValidationError(Exception):
    """Lançado quando uma entrada não passa na validação de schema."""
    pass


class KnowledgeValidator:
    """
    Valida estrutura e valores de entradas da KB.
    Não realiza nenhuma operação de I/O.
    """

    REQUIRED_FIELDS = [
        "event_id", "source", "polarity", "intensity",
        "confidence", "hair_day_rating", "themes",
        "domains", "favorable_for", "contraindications", "psychological",
    ]

    VALID_POLARITIES = {"positive", "negative", "mixed"}
    VALID_INTENSITIES = {"low", "medium", "high"}
    VALID_RATINGS = {"green", "yellow", "red"}
    VALID_PENDING_REASONS = {
        "low_confidence", "conflict", "incomplete", "interrupted", "auto_generated"
    }

    def validate_entry(self, entry: dict, context: str = "") -> None:
        """
        Valida uma entrada da KB contra o schema obrigatório.
        Lança KnowledgeValidationError se inválido.
        context: string descritiva para mensagens de erro (ex: event_id).
        """
        prefix = f"[{context}] " if context else ""

        # Campos obrigatórios presentes
        missing = [f for f in self.REQUIRED_FIELDS if f not in entry]
        if missing:
            raise KnowledgeValidationError(
                f"{prefix}Campos obrigatórios ausentes: {missing}"
            )

        # Validar polarity
        polarity = entry.get("polarity")
        if polarity not in self.VALID_POLARITIES:
            raise KnowledgeValidationError(
                f"{prefix}polarity inválido: '{polarity}'. "
                f"Válidos: {self.VALID_POLARITIES}"
            )

        # Validar intensity
        intensity = entry.get("intensity")
        if intensity not in self.VALID_INTENSITIES:
            raise KnowledgeValidationError(
                f"{prefix}intensity inválido: '{intensity}'. "
                f"Válidos: {self.VALID_INTENSITIES}"
            )

        # Validar confidence
        confidence = entry.get("confidence")
        if not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= 1.0):
            raise KnowledgeValidationError(
                f"{prefix}confidence deve ser float entre 0.0 e 1.0. Recebido: {confidence!r}"
            )

        # Validar hair_day_rating
        rating = entry.get("hair_day_rating")
        if rating not in self.VALID_RATINGS:
            raise KnowledgeValidationError(
                f"{prefix}hair_day_rating inválido: '{rating}'. "
                f"Válidos: {self.VALID_RATINGS}"
            )

        # Validar tipos de lista
        for list_field in ("themes", "domains", "favorable_for", "contraindications"):
            val = entry.get(list_field)
            if not isinstance(val, list):
                raise KnowledgeValidationError(
                    f"{prefix}'{list_field}' deve ser uma lista. Recebido: {type(val).__name__}"
                )

    def validate_pending_reason(self, reason: str) -> None:
        """Valida pending_reason. Lança KnowledgeValidationError se inválido."""
        if reason not in self.VALID_PENDING_REASONS:
            raise KnowledgeValidationError(
                f"pending_reason inválido: '{reason}'. "
                f"Válidos: {self.VALID_PENDING_REASONS}"
            )

    def is_complete(self, entry: dict) -> bool:
        """
        Retorna True se a entrada tem todos os campos required
        preenchidos e não vazios.
        """
        for f in self.REQUIRED_FIELDS:
            val = entry.get(f)
            if val is None or val == "" or val == []:
                return False
        return True

    def get_missing_fields(self, entry: dict) -> list:
        """Retorna lista de campos ausentes ou vazios."""
        missing = []
        for f in self.REQUIRED_FIELDS:
            val = entry.get(f)
            if val is None or val == "" or val == []:
                missing.append(f)
        return missing
