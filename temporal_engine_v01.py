"""
KALON ASTRO — Motor Temporal v0.1
===================================
Princípio: O tempo ativa o conhecimento.

Arquitetura:
  Knowledge Graph → Motor Temporal → Motor de Inferência → Módulo

Contrato:
  INPUT:  entidade (pontos natais) + período + eventos solicitados
  OUTPUT: lista de janelas temporais com qualidades energéticas

O Motor Temporal NÃO conhece:
  - cabelo, dieta, treino ou qualquer módulo
  - natureza (potencial/desafio) — isso é do Motor de Inferência
  - ações — isso é do módulo

O Motor Temporal SÓ entrega:
  - evento astronômico
  - janela temporal (início / pico / fim)
  - intensidade
  - qualidades energéticas (do Knowledge Graph)
"""

import swisseph as swe
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional
import json


# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

swe.set_ephe_path('/usr/share/ephe')

RESOLUCAO_MIN = 10  # granularidade do cálculo em minutos

# Planetas
LUA    = swe.MOON
SOL    = swe.SUN
VENUS  = swe.VENUS
MARTE  = swe.MARS
MERCURIO = swe.MERCURY
JUPITER  = swe.JUPITER
SATURNO  = swe.SATURN

# Aspectos maiores e seus orbes de detecção
ASPECTOS = {
    "conjuncao":  {"angulo": 0,   "orbe": 1.0},
    "sextil":     {"angulo": 60,  "orbe": 1.0},
    "quadratura": {"angulo": 90,  "orbe": 1.0},
    "trigono":    {"angulo": 120, "orbe": 1.0},
    "opposicao":  {"angulo": 180, "orbe": 1.0},
}

# Qualidades energéticas por aspecto Lua × ponto natal
QUALIDADES_ASPECTO = {
    "conjuncao":  {
        "intensidade": "maxima",
        "qualidades": ["vitalidade_elevada", "impulso_de_acao", "sensibilidade_elevada"]
    },
    "sextil":     {
        "intensidade": "moderada",
        "qualidades": ["fluxo_harmonioso", "receptividade_elevada", "assimilacao_favorecida"]
    },
    "quadratura": {
        "intensidade": "forte",
        "qualidades": ["impulso_de_acao", "sensibilidade_elevada", "resistencia_reduzida"]
    },
    "trigono":    {
        "intensidade": "forte",
        "qualidades": ["vitalidade_elevada", "regeneracao_favorecida",
                       "assimilacao_favorecida", "fluxo_harmonioso"]
    },
    "opposicao":  {
        "intensidade": "forte",
        "qualidades": ["sensibilidade_elevada", "transformacao_profunda", "recolhimento_indicado"]
    },
}

# Qualidades por fase lunar
QUALIDADES_FASE = {
    "lua_nova":       {
        "intensidade": "maxima",
        "qualidades": ["renovacao_de_ciclo", "impulso_de_acao", "receptividade_elevada"]
    },
    "lua_crescente":  {
        "intensidade": "moderada",
        "qualidades": ["vitalidade_elevada", "assimilacao_favorecida", "regeneracao_favorecida"]
    },
    "lua_cheia":      {
        "intensidade": "maxima",
        "qualidades": ["vitalidade_elevada", "receptividade_elevada", "sensibilidade_elevada"]
    },
    "lua_minguante":  {
        "intensidade": "moderada",
        "qualidades": ["recolhimento_indicado", "liberacao_de_padroes", "restauracao_profunda"]
    },
}

# Janelas padrão por tipo de evento (em minutos, configurável por módulo)
JANELAS_PADRAO = {
    "lua_aspecta_natal":  {"antes": 120, "depois": 120},
    "lua_fase":           {"antes": 720, "depois": 720},
    "lua_entra_signo":    {"antes": 60,  "depois": 180},
    "transito_planetario":{"antes": 1440,"depois": 4320},
}


# ── ESTRUTURAS DE DADOS ───────────────────────────────────────────────────────

@dataclass
class EntidadeAstrologica:
    """Pontos natais em grau decimal (0–360)."""
    id: str
    nome: str
    asc: float
    lua: float
    sol: float
    venus: float
    marte: float
    mercurio: float
    jupiter: float
    saturno: float

@dataclass
class JanelaTemporal:
    """Uma janela temporal com qualidades energéticas ativas."""
    id: str
    evento: str
    aspecto: Optional[str]
    objeto_transitante: str
    objeto_natal: str
    pico_utc: str
    inicio_utc: str
    fim_utc: str
    duracao_min: int
    intensidade: str
    qualidades: list[str]

@dataclass
class RequisicaoTemporal:
    entidade: EntidadeAstrologica
    inicio: datetime
    fim: datetime
    eventos_solicitados: list[str]
    max_horizon_dias: int = 90  # configurável por módulo
    resolucao_min: int = RESOLUCAO_MIN


# ── UTILITÁRIOS ───────────────────────────────────────────────────────────────

def jd_para_utc(jd: float) -> str:
    """Converte Tempo Juliano para string UTC ISO."""
    ut = swe.jdut1_to_utc(jd, 1)  # 1 = gregoriano
    return f"{int(ut[0]):04d}-{int(ut[1]):02d}-{int(ut[2]):02d}T{int(ut[3]):02d}:{int(ut[4]):02d}:{int(ut[5]):02d}Z"

def datetime_para_jd(dt: datetime) -> float:
    """Converte datetime UTC para Tempo Juliano."""
    return swe.julday(dt.year, dt.month, dt.day,
                      dt.hour + dt.minute/60.0 + dt.second/3600.0)

def posicao_planeta(pid: int, jd: float) -> float:
    """Retorna longitude eclíptica do planeta."""
    pos, _ = swe.calc_ut(jd, pid)
    return pos[0]

def diferenca_angular(a: float, b: float) -> float:
    """Diferença angular mínima entre dois graus (0–180)."""
    diff = abs(a - b) % 360
    return diff if diff <= 180 else 360 - diff

def detectar_aspecto(lon_transitante: float, lon_natal: float) -> Optional[tuple]:
    """Retorna (nome_aspecto, orbe) se houver aspecto, None caso contrário."""
    diff = diferenca_angular(lon_transitante, lon_natal)
    for nome, dados in ASPECTOS.items():
        orbe = abs(diff - dados["angulo"])
        if orbe <= dados["orbe"]:
            return nome, orbe
    return None


# ── MOTOR TEMPORAL v0.1 ───────────────────────────────────────────────────────

class MotorTemporal:

    def calcular(self, req: RequisicaoTemporal) -> dict:
        """
        Calcula janelas temporais para o período solicitado.
        Retorna apenas o que foi solicitado — sem cálculo especulativo.
        """
        janelas = []
        janela_id = 0

        jd_inicio = datetime_para_jd(req.inicio)
        jd_fim    = datetime_para_jd(req.fim)
        step_jd   = req.resolucao_min / (60 * 24)  # minutos → fração de dia

        # Mapear pontos natais solicitados
        pontos_natais = self._mapear_pontos(req.entidade)

        # ── EVENTO: lua_aspecta_*_natal ───────────────────────────────────────
        eventos_aspecto = [e for e in req.eventos_solicitados
                           if e.startswith("lua_aspecta_")]

        if eventos_aspecto:
            jd = jd_inicio
            lon_lua_prev = posicao_planeta(LUA, jd)
            aspecto_ativo = {}  # ponto_natal → aspecto ativo atual

            while jd <= jd_fim:
                lon_lua = posicao_planeta(LUA, jd)

                for evento_id in eventos_aspecto:
                    ponto = evento_id.replace("lua_aspecta_", "").replace("_natal", "")
                    if ponto not in pontos_natais:
                        continue
                    lon_natal = pontos_natais[ponto]

                    resultado = detectar_aspecto(lon_lua, lon_natal)

                    if resultado:
                        nome_asp, orbe = resultado
                        chave = f"{ponto}_{nome_asp}"
                        # Só registra se é novo evento (não estava ativo)
                        if chave not in aspecto_ativo:
                            aspecto_ativo[chave] = {
                                "jd_pico": jd, "orbe_min": orbe,
                                "ponto": ponto, "aspecto": nome_asp,
                                "evento_id": evento_id
                            }
                        elif orbe < aspecto_ativo[chave]["orbe_min"]:
                            aspecto_ativo[chave]["jd_pico"] = jd
                            aspecto_ativo[chave]["orbe_min"] = orbe
                    else:
                        chave = f"{ponto}_{nome_asp}" if resultado else None
                        # Fechar eventos que terminaram
                        for k in list(aspecto_ativo.keys()):
                            if k.startswith(f"{ponto}_"):
                                ev = aspecto_ativo.pop(k)
                                janela_id += 1
                                janelas.append(
                                    self._criar_janela_aspecto(janela_id, ev, "lua"))

                jd += step_jd
                lon_lua_prev = lon_lua

        # ── EVENTO: lua_fase ──────────────────────────────────────────────────
        if "lua_fase" in req.eventos_solicitados:
            fase_janelas = self._calcular_fases_lunares(
                jd_inicio, jd_fim, step_jd)
            for f in fase_janelas:
                janela_id += 1
                f["id"] = f"jt_{janela_id:04d}"
                janelas.append(JanelaTemporal(**f))

        # Ordenar por pico
        janelas.sort(key=lambda j: j.pico_utc)

        return {
            "entidade":    req.entidade.nome,
            "periodo":     {"inicio": req.inicio.isoformat(), "fim": req.fim.isoformat()},
            "total_janelas": len(janelas),
            "janelas":     [self._serializar(j) for j in janelas],
        }

    def _mapear_pontos(self, ent: EntidadeAstrologica) -> dict:
        return {
            "asc": ent.asc, "lua": ent.lua, "sol": ent.sol,
            "venus": ent.venus, "marte": ent.marte,
            "mercurio": ent.mercurio, "jupiter": ent.jupiter,
            "saturno": ent.saturno,
        }

    def _criar_janela_aspecto(self, jid: int, ev: dict, obj_transit: str) -> JanelaTemporal:
        q = QUALIDADES_ASPECTO[ev["aspecto"]]
        cfg = JANELAS_PADRAO["lua_aspecta_natal"]
        jd_pico = ev["jd_pico"]
        jd_ini  = jd_pico - cfg["antes"] / (60 * 24)
        jd_fim  = jd_pico + cfg["depois"] / (60 * 24)
        return JanelaTemporal(
            id=f"jt_{jid:04d}",
            evento=ev["evento_id"],
            aspecto=ev["aspecto"],
            objeto_transitante=obj_transit,
            objeto_natal=ev["ponto"],
            pico_utc=jd_para_utc(jd_pico),
            inicio_utc=jd_para_utc(jd_ini),
            fim_utc=jd_para_utc(jd_fim),
            duracao_min=cfg["antes"] + cfg["depois"],
            intensidade=q["intensidade"],
            qualidades=q["qualidades"],
        )

    def _calcular_fases_lunares(self, jd_ini, jd_fim, step) -> list:
        """Detecta mudanças de fase lunar no período."""
        janelas = []
        fases = {0: "lua_nova", 90: "lua_crescente",
                 180: "lua_cheia", 270: "lua_minguante"}
        fase_prev = None
        jd = jd_ini
        while jd <= jd_fim:
            lon_lua = posicao_planeta(LUA, jd)
            lon_sol = posicao_planeta(SOL, jd)
            ang = (lon_lua - lon_sol) % 360
            quadrante = int(ang / 90) * 90
            fase_atual = fases.get(quadrante)
            if fase_atual and fase_atual != fase_prev:
                q = QUALIDADES_FASE[fase_atual]
                cfg = JANELAS_PADRAO["lua_fase"]
                janelas.append({
                    "evento": fase_atual,
                    "aspecto": None,
                    "objeto_transitante": "lua",
                    "objeto_natal": "fase_lunar",
                    "pico_utc": jd_para_utc(jd),
                    "inicio_utc": jd_para_utc(jd - cfg["antes"]/(60*24)),
                    "fim_utc": jd_para_utc(jd + cfg["depois"]/(60*24)),
                    "duracao_min": cfg["antes"] + cfg["depois"],
                    "intensidade": q["intensidade"],
                    "qualidades": q["qualidades"],
                })
                fase_prev = fase_atual
            jd += step
        return janelas

    def _serializar(self, j: JanelaTemporal) -> dict:
        return {
            "id":                  j.id,
            "evento":              j.evento,
            "aspecto":             j.aspecto,
            "objeto_transitante":  j.objeto_transitante,
            "objeto_natal":        j.objeto_natal,
            "pico_utc":            j.pico_utc,
            "inicio_utc":          j.inicio_utc,
            "fim_utc":             j.fim_utc,
            "duracao_min":         j.duracao_min,
            "intensidade":         j.intensidade,
            "qualidades":          j.qualidades,
        }


# ── TESTE: ROBERTO GAMA — JULHO 2026 ─────────────────────────────────────────

if __name__ == "__main__":
    # Mapa natal de Roberto Gama (calculado via pyswisseph)
    roberto = EntidadeAstrologica(
        id="roberto_gama",
        nome="Roberto Gama",
        asc=26.4,      # Touro
        lua=198.7,     # Libra
        sol=155.9,     # Virgem
        venus=201.3,   # Libra
        marte=161.2,   # Virgem
        mercurio=162.1,# Virgem
        jupiter=204.5, # Libra
        saturno=249.1, # Sagitário
    )

    req = RequisicaoTemporal(
        entidade=roberto,
        inicio=datetime(2026, 7, 1, tzinfo=timezone.utc),
        fim=datetime(2026, 7, 31, tzinfo=timezone.utc),
        eventos_solicitados=[
            "lua_aspecta_asc_natal",
            "lua_aspecta_lua_natal",
            "lua_fase",
        ],
        resolucao_min=10,
    )

    motor = MotorTemporal()
    resultado = motor.calcular(req)

    print(f"Motor Temporal v0.1 — {resultado['entidade']}")
    print(f"Período: Julho 2026")
    print(f"Janelas encontradas: {resultado['total_janelas']}")
    print()

    # Formato tabela — como o usuário verá
    print(f"{'DATA/HORA PICO':<20} {'EVENTO':<28} {'INTENSIDADE':<12} {'QUALIDADES'}")
    print("─" * 100)
    for j in resultado["janelas"][:15]:  # primeiras 15
        pico = j["pico_utc"][:16].replace("T", " ")
        ev   = j["evento"].replace("_", " ")
        asp  = f"({j['aspecto']})" if j["aspecto"] else ""
        qs   = ", ".join(j["qualidades"][:2])  # primeiras 2 qualidades
        print(f"{pico:<20} {ev+' '+asp:<28} {j['intensidade']:<12} {qs}")

    print()
    print("── PRIMEIRA JANELA — ESTRUTURA COMPLETA ──")
    print(json.dumps(resultado["janelas"][0], indent=2, ensure_ascii=False))
