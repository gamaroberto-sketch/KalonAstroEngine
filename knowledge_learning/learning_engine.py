"""
Kalon Astro Engine — LearningEngine
Motor de persistência e consulta das observações puras (fatos).
"""

import os
import yaml
from datetime import datetime
from collections import Counter


class LearningEngine:
    """
    Gerencia a leitura e escrita do observations.yaml.
    As observações são imutáveis após criadas.
    """
    def __init__(self, base_path: str = None):
        if not base_path:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._obs_file = os.path.join(base_path, "knowledge_learning", "observations.yaml")

    def _read_file(self) -> dict:
        if not os.path.exists(self._obs_file):
            return {"metadata": {}, "observations": []}
        with open(self._obs_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else {"metadata": {}, "observations": []}

    def _write_file(self, data: dict):
        with open(self._obs_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    def log_observation(self, obs: dict) -> str:
        """
        Recebe um dicionário de observação, injeta o ID sequencial
        e timestamp, e salva no observations.yaml.
        """
        data = self._read_file()
        obs_list = data.setdefault("observations", [])
        
        # Gerar ID sequencial
        count = len(obs_list) + 1
        new_id = f"OBS_{count:03d}"
        
        obs["id"] = new_id
        if "registered_at" not in obs:
            obs["registered_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
        obs_list.append(obs)
        self._write_file(data)
        return new_id

    def get_observations(self, event_id: str = None) -> list:
        """
        Retorna observações. Se event_id for fornecido, filtra por ele.
        """
        data = self._read_file()
        obs_list = data.get("observations", [])
        if event_id:
            return [o for o in obs_list if o.get("event_id") == event_id]
        return obs_list

    def get_all_observations(self) -> list:
        return self.get_observations()

    def get_ready_for_update(self, min_obs: int = 3, after_id: str = "OBS_000") -> list:
        """
        Retorna event_ids que têm min_obs ou mais observações novas 
        (com ID maior que after_id).
        """
        data = self._read_file()
        obs_list = data.get("observations", [])
        
        # Filtrar observações novas
        new_obs = [o for o in obs_list if o.get("id", "") > after_id]
        
        # Contar por event_id
        counts = Counter(o.get("event_id") for o in new_obs)
        return [eid for eid, count in counts.items() if count >= min_obs]

    def get_statistics(self) -> dict:
        obs_list = self.get_all_observations()
        val_counts = Counter(o.get("user_validation", "unknown") for o in obs_list)
        return {
            "total_observations": len(obs_list),
            "by_validation": dict(val_counts)
        }
