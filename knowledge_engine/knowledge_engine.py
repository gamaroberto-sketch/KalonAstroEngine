"""
Kalon Astro Engine — Knowledge Engine
Fase 5: Motor de Conhecimento.

Carrega pacotes de conhecimento astrológico (YAML) e os executa
contra eventos do Timeline Engine.

Camadas:
  - Engine (Python): executa regras. Não sabe nada sobre produtos.
  - Knowledge (YAML): contém o conhecimento astrológico por produto.

O Engine não conhece AstroHair, AstroDiet, AstroCash ou AstroLove.
Ele apenas carrega, valida e executa o que os pacotes definem.
"""

import yaml
import os
from typing import Optional


# ─── Exceções ────────────────────────────────────────────

class KnowledgeValidationError(Exception):
    """Levantada quando um arquivo YAML viola o schema obrigatório."""
    pass


class KnowledgePackageNotFound(Exception):
    """Levantada quando o produto solicitado não existe em knowledge/."""
    pass


# ─── Campos obrigatórios por regra ───────────────────────

REQUIRED_FIELDS = ["id", "product", "name", "conditions", "score", "message"]

# ─── Caminho base dos pacotes ─────────────────────────────

_KNOWLEDGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "knowledge"
)


# ─── Carregamento e validação ─────────────────────────────

def _validate_rule(rule: dict, source_file: str) -> None:
    """Valida que a regra contém todos os campos obrigatórios."""
    for field in REQUIRED_FIELDS:
        if field not in rule:
            raise KnowledgeValidationError(
                f"Regra '{rule.get('id', '?')}' em '{source_file}' "
                f"está faltando o campo obrigatório: '{field}'"
            )


def load_package(product: str) -> dict:
    """
    Carrega e valida um pacote de conhecimento completo.

    Parâmetros:
        product: nome do produto em minúsculas (ex: 'astrohair')

    Retorna:
        dict com: rules, weights, metadata
    """
    package_path = os.path.join(_KNOWLEDGE_PATH, product.lower())

    if not os.path.isdir(package_path):
        raise KnowledgePackageNotFound(
            f"Pacote '{product}' não encontrado em knowledge/. "
            f"Crie a pasta 'knowledge/{product.lower()}/' com rules.yaml."
        )

    # Carregar rules.yaml (obrigatório)
    rules_path = os.path.join(package_path, "rules.yaml")
    if not os.path.exists(rules_path):
        raise KnowledgeValidationError(f"'{product}' não possui rules.yaml")

    with open(rules_path, encoding="utf-8") as f:
        rules_data = yaml.safe_load(f)

    rules = rules_data.get("rules", [])
    for rule in rules:
        _validate_rule(rule, rules_path)

    # Carregar weights.yaml (opcional)
    weights_path = os.path.join(package_path, "weights.yaml")
    weights = {}
    if os.path.exists(weights_path):
        with open(weights_path, encoding="utf-8") as f:
            weights = yaml.safe_load(f) or {}

    # Carregar metadata.yaml (opcional)
    metadata_path = os.path.join(package_path, "metadata.yaml")
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, encoding="utf-8") as f:
            metadata = yaml.safe_load(f) or {}

    # Filtrar apenas regras ativas
    active_rules = [r for r in rules if r.get("active", True)]

    return {
        "product": product,
        "rules": active_rules,
        "weights": weights,
        "metadata": metadata
    }


# ─── Avaliação de condições ───────────────────────────────

def _evaluate_conditions(conditions: dict, event: dict) -> bool:
    """
    Verifica se as condições de uma regra são satisfeitas pelo evento.

    O evento é um instante do Timeline Engine:
    {
        "datetime": "...",
        "planets": { "MOON": {...}, ... },
        "aspects": [ {...}, ... ]
    }
    """
    aspects = event.get("aspects", [])
    planets = event.get("planets", {})

    # Condição: aspecto específico presente
    if "aspect" in conditions:
        aspect_id = conditions["aspect"]
        phase_req = conditions.get("phase")
        max_orb = conditions.get("max_orb")
        min_precision = conditions.get("min_precision")

        aspect_found = False
        for asp in aspects:
            if asp.get("id") == aspect_id:
                if phase_req and asp.get("phase") != phase_req:
                    continue
                if max_orb is not None and asp.get("orbe", 999) > max_orb:
                    continue
                if min_precision is not None and asp.get("precisao", 0) < min_precision:
                    continue
                aspect_found = True
                break

        if not aspect_found:
            return False

    # Condição: objeto específico em signo específico
    if "planet_sign" in conditions:
        ps = conditions["planet_sign"]
        planet_id = ps.get("planet")
        sign_req = ps.get("sign")
        planet_data = planets.get(planet_id, {})
        if planet_data.get("signo") != sign_req:
            return False

    # Condição: planeta retrógrado
    if "planet_retro" in conditions:
        planet_id = conditions["planet_retro"]
        planet_data = planets.get(planet_id, {})
        speed = planet_data.get("speed_longitude", 1.0)
        if speed >= 0:
            return False

    # Condição: phase lunar (futura — placeholder para Fase 5.1)
    if "moon_phase" in conditions:
        # TODO: implementar cálculo de fase lunar no Astro Engine
        pass

    return True


# ─── Execução principal ───────────────────────────────────

def execute(event: dict, package: dict) -> dict:
    """
    Executa o pacote de conhecimento contra um evento do Timeline.

    Parâmetros:
        event: instante do Timeline Engine
        package: pacote carregado por load_package()

    Retorna:
        {
            "datetime": "...",
            "product": "astrohair",
            "total_score": {"beauty": 30, "growth": 20, "strength": 8},
            "triggered_rules": [ {rule + score} ],
            "messages": ["...", "..."]
        }
    """
    triggered = []
    total_score = {}
    messages = []

    for rule in package["rules"]:
        conditions = rule.get("conditions", {})

        if _evaluate_conditions(conditions, event):
            triggered.append({
                "id": rule["id"],
                "name": rule["name"],
                "score": rule["score"],
                "message": rule["message"],
                "confidence": rule.get("confidence", 1.0),
                "evidence": rule.get("evidence", [])
            })

            messages.append(rule["message"])

            # Acumular score por dimensão
            for dimension, value in rule["score"].items():
                total_score[dimension] = total_score.get(dimension, 0) + value

    return {
        "datetime": event.get("datetime"),
        "product": package["product"],
        "total_score": total_score,
        "triggered_rules": triggered,
        "messages": messages
    }
