import math
import swisseph as swe

PLANETAS = {
    'sol':      swe.SUN,
    'lua':      swe.MOON,
    'mercurio': swe.MERCURY,
    'venus':    swe.VENUS,
    'marte':    swe.MARS,
    'jupiter':  swe.JUPITER,
    'saturno':  swe.SATURN,
}

def resolver_transitante(cfg_transitante, jd: float) -> tuple[float, str]:
    """
    Resolve a longitude do transitante para um dado instante (jd).
    Retorna (longitude_graus, nome_display).
    
    cfg_transitante pode ser:
      - string simples: "lua", "venus", "marte" etc (retrocompatível)
      - dict estruturado: {tipo: objeto, objeto: {tipo: midpoint, componentes: [...]}}
    """
    if isinstance(cfg_transitante, str):
        nome = cfg_transitante.lower()
        pid = PLANETAS.get(nome, swe.MOON)
        pos, _ = swe.calc_ut(jd, pid)
        return pos[0], nome.capitalize()

    if isinstance(cfg_transitante, dict):
        tipo_obj = cfg_transitante.get('objeto', {}).get('tipo')
        
        if tipo_obj == 'midpoint':
            componentes = cfg_transitante['objeto'].get('componentes', [])
            if len(componentes) != 2:
                raise ValueError(f"Midpoint requer exatamente 2 componentes, recebeu {len(componentes)}")
            
            p1 = componentes[0].lower()
            p2 = componentes[1].lower()
            pid1 = PLANETAS.get(p1)
            pid2 = PLANETAS.get(p2)
            if pid1 is None or pid2 is None:
                raise ValueError(f"Planeta desconhecido em midpoint: {p1} ou {p2}")
            
            pos1, _ = swe.calc_ut(jd, pid1)
            pos2, _ = swe.calc_ut(jd, pid2)
            lon1, lon2 = pos1[0], pos2[0]
            
            # MÉDIA ANGULAR VETORIAL (nunca aritmética simples):
            lon1_rad = math.radians(lon1)
            lon2_rad = math.radians(lon2)
            x = math.cos(lon1_rad) + math.cos(lon2_rad)
            y = math.sin(lon1_rad) + math.sin(lon2_rad)
            midpoint = math.degrees(math.atan2(y, x)) % 360
            if midpoint >= 360.0:
                midpoint = midpoint - 360.0
            
            nome_display = f"{p1.capitalize()}/{p2.capitalize()}"
            return midpoint, nome_display
        
        raise ValueError(f"Tipo de objeto desconhecido: {tipo_obj}")

    raise ValueError("Formato de transitante inválido.")
