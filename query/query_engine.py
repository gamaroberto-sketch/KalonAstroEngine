"""
Kalon Astro Engine — Query Engine
Fase 3: Motor de Consulta Universal.

Não calcula, apenas consulta o output do Astro Engine e Aspect Engine.
Regra rígida: Apenas métodos acessíveis via `.execute("query", **kwargs)`.
"""

class QueryNotFoundError(Exception):
    """Exceção levantada quando a query solicitada não existe no engine."""
    pass


class QueryEngine:
    def __init__(self, chart: dict, aspects: list):
        self.chart = chart
        self.aspects = aspects
        self.planetas = chart.get("planetas", {})
        
        # Mapeamento bidirecional para normalização de IDs e Nomes
        self.id_to_name = {
            "SUN": "Sol", "MOON": "Lua", "MER": "Mercúrio", "VEN": "Vênus",
            "MAR": "Marte", "JUP": "Júpiter", "SAT": "Saturno", "URA": "Urano",
            "NEP": "Netuno", "PLU": "Plutão"
        }
        
        self.name_map = {}
        for pid, pname in self.id_to_name.items():
            self.name_map[pid.lower()] = pname
            self.name_map[pname.lower()] = pname
            
    def _normalize_planet(self, identifier: str) -> str:
        """Retorna o nome do planeta normalizado em português (ex: 'Sol')."""
        if not identifier:
            return ""
        mapped = self.name_map.get(identifier.lower())
        if mapped:
            return mapped
        return identifier # Fallback

    def _normalize_planet_id(self, identifier: str) -> str:
        """Retorna o ID do planeta normalizado (ex: 'SUN')."""
        name = self._normalize_planet(identifier)
        for k, v in self.id_to_name.items():
            if v == name:
                return k
        return identifier

    def execute(self, query_name: str, **kwargs):
        """
        Roteador principal de queries.
        Mapeia a string da consulta para o método interno correspondente.
        """
        method = getattr(self, f"query_{query_name}", None)
        if not method or not callable(method):
            raise QueryNotFoundError(f"Query '{query_name}' não foi encontrada no motor.")
        return method(**kwargs)

    # =========================================================================
    # QUERIES IMPLEMENTADAS
    # =========================================================================

    def query_aspectos_de(self, planeta: str) -> list:
        pid = self._normalize_planet_id(planeta)
        pname = self._normalize_planet(planeta)
        return [
            a for a in self.aspects 
            if a.get("object1_id") == pid or a.get("object2_id") == pid or 
               a.get("object1_id") == pname or a.get("object2_id") == pname
        ]

    def query_existe_aspecto(self, planeta1: str, planeta2: str = None, tipo: str = None) -> bool:
        aspects = self.query_aspectos_de(planeta1)
        
        if planeta2:
            p2id = self._normalize_planet_id(planeta2)
            p2name = self._normalize_planet(planeta2)
            aspects = [
                a for a in aspects 
                if a.get("object1_id") == p2id or a.get("object2_id") == p2id or 
                   a.get("object1_id") == p2name or a.get("object2_id") == p2name
            ]
            
        if tipo:
            aspects = [a for a in aspects if a.get("tipo", "").lower() == tipo.lower()]
            
        return len(aspects) > 0

    def query_aspectos_por_tipo(self, tipo: str) -> list:
        return [a for a in self.aspects if a.get("tipo", "").lower() == tipo.lower()]

    def query_aspectos_por_orbe(self, max_orbe: float) -> list:
        return [a for a in self.aspects if a.get("orbe", 999) <= max_orbe]

    def query_aspectos_harmonicos(self) -> list:
        return [a for a in self.aspects if a.get("harmonico") is True]

    def query_aspectos_tensos(self) -> list:
        return [a for a in self.aspects if a.get("harmonico") is False]

    def query_aspectos_por_phase(self, phase: str) -> list:
        return [a for a in self.aspects if a.get("phase", "").lower() == phase.lower()]

    def query_planeta_em_signo(self, planeta: str) -> dict:
        pname = self._normalize_planet(planeta)
        if pname in self.planetas:
            return self.planetas[pname]
        return {}

    def query_planetas_em_signo(self, signo: str) -> list:
        return [pname for pname, data in self.planetas.items() if data.get("signo", "").lower() == signo.lower()]

    def query_planeta_retrogrado(self, planeta: str) -> bool:
        pname = self._normalize_planet(planeta)
        if pname in self.planetas:
            return self.planetas[pname].get("retrogrado", False)
        return False

    def query_planetas_retrogrados(self) -> list:
        return [pname for pname, data in self.planetas.items() if data.get("retrogrado", False)]

    def query_casa_do_planeta(self, planeta: str) -> int:
        pname = self._normalize_planet(planeta)
        if pname not in self.planetas:
            return 0
        
        lon = self.planetas[pname]["longitude"]
        casas = self.chart.get("casas", {})
        
        # Extrair e ordenar cúspides
        house_cusps = []
        for i in range(1, 13):
            k = f"Casa {i}"
            if k in casas:
                house_cusps.append((i, casas[k]["longitude"]))
                
        if not house_cusps:
            return 0
            
        for i in range(12):
            h_num, cusp = house_cusps[i]
            next_h_num, next_cusp = house_cusps[(i + 1) % 12]
            
            # Verifica se está contido na faixa do grau
            if cusp < next_cusp:
                if cusp <= lon < next_cusp:
                    return h_num
            else:
                if lon >= cusp or lon < next_cusp:
                    return h_num
                    
        return 0

    def query_planetas_na_casa(self, casa: int) -> list:
        found = []
        for pname in self.planetas:
            if self.query_casa_do_planeta(pname) == casa:
                found.append(pname)
        return found
        
    def query_resumo_mapa(self) -> dict:
        retrogrados = self.query_planetas_retrogrados()
        
        # Cálculo de stelliums (3 ou mais planetas no mesmo signo)
        sign_counts = {}
        for pname, data in self.planetas.items():
            signo = data.get("signo")
            if signo:
                sign_counts[signo] = sign_counts.get(signo, 0) + 1
        
        stellium = [signo for signo, count in sign_counts.items() if count >= 3]
        
        return {
            "total_aspectos": len(self.aspects),
            "harmonicos": len(self.query_aspectos_harmonicos()),
            "tensos": len(self.query_aspectos_tensos()),
            "retrogrados": retrogrados,
            "stellium": stellium
        }
