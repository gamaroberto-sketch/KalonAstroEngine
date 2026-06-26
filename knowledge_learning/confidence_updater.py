"""
Kalon Astro Engine — ConfidenceUpdater
Motor de cálculo que traduz observações em deltas baseados no confidence_model.yaml.
"""

import os
import yaml
from datetime import datetime
from knowledge_learning.learning_engine import LearningEngine
from knowledge.repository import KnowledgeRepository


class ConfidenceUpdater:
    def __init__(self, learning_engine: LearningEngine, repository: KnowledgeRepository, base_path: str = None):
        self._engine = learning_engine
        self._repo = repository
        
        if not base_path:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._model_file = os.path.join(base_path, "knowledge_base", "confidence_model.yaml")
        
        with open(self._model_file, "r", encoding="utf-8") as f:
            self._model = yaml.safe_load(f)

    def _get_rules(self) -> dict:
        return self._model.get("rules", {})

    def _save_model_state(self, processed_id: str):
        self._model["processed_up_to_obs_id"] = processed_id
        self._model["last_update_applied"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        with open(self._model_file, "w", encoding="utf-8") as f:
            yaml.dump(self._model, f, sort_keys=False, allow_unicode=True)

    def calculate_delta(self, event_id: str) -> float:
        """
        Calcula o delta de confidence para as observações não processadas de um event_id.
        """
        rules = self._get_rules()
        processed_up_to = self._model.get("processed_up_to_obs_id", "OBS_000")
        
        all_obs = self._engine.get_observations(event_id)
        # Apenas observações que ainda não foram processadas
        new_obs = [o for o in all_obs if o.get("id", "") > processed_up_to]
        
        if not new_obs:
            return 0.0

        raw_delta = 0.0
        for obs in new_obs:
            val = obs.get("user_validation")
            if val == "confirmed":
                raw_delta += rules.get("confirmed_delta", 0.01)
            elif val == "partial":
                raw_delta += rules.get("partial_delta", 0.00)
            elif val == "diverged":
                raw_delta += rules.get("diverged_delta", -0.02)
                
        # Limite por sessão
        max_delta = rules.get("max_delta_per_session", 0.05)
        clamped_delta = max(-max_delta, min(max_delta, raw_delta))
        return clamped_delta

    def propose_updates(self) -> list:
        """
        Retorna propostas de atualização para os event_ids que atingiram min_observations.
        """
        rules = self._get_rules()
        min_obs = rules.get("min_observations_to_update", 3)
        processed_up_to = self._model.get("processed_up_to_obs_id", "OBS_000")
        
        ready_events = self._engine.get_ready_for_update(min_obs, after_id=processed_up_to)
        
        approved_kb = self._repo._loader.load_approved()
        
        proposals = []
        for eid in ready_events:
            entry = approved_kb.get(eid)
            if not entry:
                continue
                
            current_conf = float(entry.get("confidence", 0.80))
            delta = self.calculate_delta(eid)
            new_conf = current_conf + delta
            
            # Limites
            new_conf = max(rules.get("confidence_floor", 0.50), min(rules.get("confidence_ceiling", 0.99), new_conf))
            new_conf = round(new_conf, 2)
            
            all_obs = self._engine.get_observations(eid)
            new_obs = [o for o in all_obs if o.get("id", "") > processed_up_to]
            
            proposals.append({
                "event_id": eid,
                "current_confidence": current_conf,
                "proposed_confidence": new_conf,
                "delta": round(new_conf - current_conf, 2),
                "obs_count": len(new_obs)
            })
            
        return proposals

    def apply_updates(self, reviewer: str) -> list:
        """
        Aplica os updates na KB, gera log no journal e atualiza o estado do modelo.
        """
        proposals = self.propose_updates()
        if not proposals:
            return []
            
        # Atualizar a KB via Repository
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        for prop in proposals:
            eid = prop["event_id"]
            # Lê o entry inteiro, atualiza confidence e faz update
            # O repositório já se encarrega de salvar
            # Para isso, usamos update no repository
            approved_kb = self._repo._loader.load_approved()
            entry = approved_kb[eid]
            entry["confidence"] = prop["proposed_confidence"]
            # Para registrar notas/reasoning
            entry["notes"] = f"Confidence ajustada pelo Learning Engine: {prop['current_confidence']} -> {prop['proposed_confidence']} (baseado em {prop['obs_count']} observacoes recentes)"
            self._repo.update(eid, entry, reviewer, ts)

        # Encontrar o maior ID processado globalmente
        all_obs = self._engine.get_all_observations()
        if all_obs:
            max_id = max(o.get("id", "") for o in all_obs)
            self._save_model_state(max_id)
            
        return proposals
