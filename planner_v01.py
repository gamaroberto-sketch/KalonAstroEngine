"""
KALON ASTRO — Planejador v0.1
==============================
Quarto serviço do Kalon Astro Engine.
Responsabilidade única: receber janelas temporais e montar ações concretas.

Arquitetura:
  Knowledge Graph → Motor Temporal → Motor de Inferência → Planejador → Módulo

O Planejador:
  - Recebe: janelas do Motor Temporal (qualidades energéticas)
  - Consulta: objetivos, evidências e recomendações do Knowledge Graph
  - Entrega: lista de ações com data/hora/janela/rastro auditável

O Planejador NÃO sabe nada de astrologia.
Ele só sabe mapear qualidades → ações via módulo declarado.
"""

import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional


# ── MAPEAMENTO DE QUALIDADES → AÇÕES (declarado pelo módulo AstroHair) ────────
# Cada módulo declara seu próprio mapeamento.
# O Planejador é agnóstico — só executa o mapeamento recebido.

MODULO_ASTROHAIR = {
    "id": "astrohair",
    "nome": "AstroHair",

    # Regras: lista de qualidades necessárias → ação
    # O Planejador verifica se TODAS as qualidades da regra estão na janela
    "regras": [
        {
            "qualidades_necessarias": ["vitalidade_elevada", "regeneracao_favorecida"],
            "acao": {
                "emoji": "✂️",
                "texto": "Corte para estimular crescimento",
                "objetivo": "estimular_crescimento",
                "evidencia": "ciclo_capilar",
                "indicador": "crescimento_capilar",
                "prioridade": 1,
            }
        },
        {
            "qualidades_necessarias": ["receptividade_elevada", "assimilacao_favorecida"],
            "acao": {
                "emoji": "💧",
                "texto": "Hidratação profunda — boa absorção",
                "objetivo": "melhorar_hidratacao",
                "evidencia": "hidratacao",
                "indicador": "hidratacao_capilar",
                "prioridade": 1,
            }
        },
        {
            "qualidades_necessarias": ["assimilacao_favorecida", "fluxo_harmonioso"],
            "acao": {
                "emoji": "🧴",
                "texto": "Máscara nutritiva — momento de boa absorção",
                "objetivo": "fortalecer_foliculo",
                "evidencia": "ciclo_capilar",
                "indicador": "crescimento_capilar",
                "prioridade": 2,
            }
        },
        {
            "qualidades_necessarias": ["sensibilidade_elevada", "resistencia_reduzida"],
            "acao": {
                "emoji": "🚫",
                "texto": "Evite química agressiva — couro cabeludo sensível",
                "objetivo": "reduzir_inflamacao",
                "evidencia": "inflamacao",
                "indicador": "inflamacao_capilar",
                "prioridade": 1,
            }
        },
        {
            "qualidades_necessarias": ["recolhimento_indicado"],
            "acao": {
                "emoji": "⏸",
                "texto": "Evite procedimentos — fase de recolhimento",
                "objetivo": "retardar_envelhecimento",
                "evidencia": "ciclo_capilar",
                "indicador": "envelhecimento_capilar",
                "prioridade": 2,
            }
        },
        {
            "qualidades_necessarias": ["renovacao_de_ciclo", "impulso_de_acao"],
            "acao": {
                "emoji": "🌱",
                "texto": "Início de novo ciclo — boa janela para tratamento regenerativo",
                "objetivo": "estimular_crescimento",
                "evidencia": "ciclo_capilar",
                "indicador": "crescimento_capilar",
                "prioridade": 1,
            }
        },
        {
            "qualidades_necessarias": ["liberacao_de_padroes", "restauracao_profunda"],
            "acao": {
                "emoji": "🧹",
                "texto": "Limpeza profunda — boa janela para desintoxicação capilar",
                "objetivo": "reduzir_inflamacao",
                "evidencia": "regulacao_sebacea",
                "indicador": "oleosidade_capilar",
                "prioridade": 2,
            }
        },
        {
            "qualidades_necessarias": ["transformacao_profunda"],
            "acao": {
                "emoji": "🔄",
                "texto": "Revisão de rotina capilar — momento de mudança de estratégia",
                "objetivo": "retardar_envelhecimento",
                "evidencia": "envelhecimento_estrutural",
                "indicador": "envelhecimento_capilar",
                "prioridade": 3,
            }
        },
    ]
}


# ── PLANEJADOR ────────────────────────────────────────────────────────────────

@dataclass
class AcaoPlanejada:
    janela_id: str
    evento: str
    aspecto: Optional[str]
    pico_utc: str
    inicio_utc: str
    fim_utc: str
    intensidade: str
    qualidades_ativas: list[str]
    # Ação
    emoji: str
    texto: str
    objetivo: str
    evidencia: str
    indicador: str
    prioridade: int


class Planejador:
    """
    Responsabilidade única: mapear janelas temporais → ações concretas.
    Agnóstico ao módulo — executa o mapeamento declarado pelo módulo.
    """

    def planejar(self, janelas: list[dict], modulo: dict,
                 fuso_offset_h: int = -3) -> dict:
        """
        janelas: saída do Motor Temporal
        modulo:  declaração do módulo (regras de mapeamento)
        fuso_offset_h: offset do fuso local em horas (padrão: BRT -3)
        """
        acoes = []

        for janela in janelas:
            qualidades_janela = set(janela["qualidades"])

            for regra in modulo["regras"]:
                necessarias = set(regra["qualidades_necessarias"])
                # Verifica se TODAS as qualidades necessárias estão na janela
                if necessarias.issubset(qualidades_janela):
                    acoes.append(AcaoPlanejada(
                        janela_id=janela["id"],
                        evento=janela["evento"],
                        aspecto=janela.get("aspecto"),
                        pico_utc=janela["pico_utc"],
                        inicio_utc=janela["inicio_utc"],
                        fim_utc=janela["fim_utc"],
                        intensidade=janela["intensidade"],
                        qualidades_ativas=janela["qualidades"],
                        emoji=regra["acao"]["emoji"],
                        texto=regra["acao"]["texto"],
                        objetivo=regra["acao"]["objetivo"],
                        evidencia=regra["acao"]["evidencia"],
                        indicador=regra["acao"]["indicador"],
                        prioridade=regra["acao"]["prioridade"],
                    ))
                    break  # uma ação por janela (a primeira regra que casar)

        # Ordenar por data do pico
        acoes.sort(key=lambda a: a.pico_utc)

        return {
            "modulo":        modulo["id"],
            "total_acoes":   len(acoes),
            "fuso_offset_h": fuso_offset_h,
            "agenda":        [self._serializar(a, fuso_offset_h) for a in acoes],
        }

    def _serializar(self, a: AcaoPlanejada, offset: int) -> dict:
        """Serializa com horários locais e rastro auditável completo."""
        pico   = self._utc_para_local(a.pico_utc,   offset)
        inicio = self._utc_para_local(a.inicio_utc, offset)
        fim    = self._utc_para_local(a.fim_utc,    offset)

        return {
            # O que o usuário vê
            "data":         pico[:10],
            "hora_pico":    pico[11:16],
            "janela":       f"{inicio[11:16]}–{fim[11:16]}",
            "emoji":        a.emoji,
            "acao":         a.texto,
            "intensidade":  a.intensidade,

            # Rastro auditável (expandível na UI)
            "auditoria": {
                "janela_id":        a.janela_id,
                "evento":           a.evento,
                "aspecto":          a.aspecto,
                "qualidades_ativas": a.qualidades_ativas,
                "objetivo":         a.objetivo,
                "evidencia":        a.evidencia,
                "indicador":        a.indicador,
                "prioridade":       a.prioridade,
                "pico_utc":         a.pico_utc,
                "inicio_utc":       a.inicio_utc,
                "fim_utc":          a.fim_utc,
            }
        }

    def _utc_para_local(self, ts_utc: str, offset_h: int) -> str:
        """Converte timestamp UTC para horário local."""
        dt = datetime.fromisoformat(ts_utc.replace("Z", "+00:00"))
        dt_local = dt + timedelta(hours=offset_h)
        return dt_local.strftime("%Y-%m-%d %H:%M")


# ── TESTE INTEGRADO: Motor Temporal + Planejador ─────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/home/claude')
    from temporal_engine_v01 import (
        MotorTemporal, RequisicaoTemporal, EntidadeAstrologica
    )

    # 1. Motor Temporal calcula as janelas
    roberto = EntidadeAstrologica(
        id="roberto_gama", nome="Roberto Gama",
        asc=26.4, lua=198.7, sol=155.9, venus=201.3,
        marte=161.2, mercurio=162.1, jupiter=204.5, saturno=249.1,
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
    resultado_temporal = motor.calcular(req)

    # 2. Planejador mapeia janelas → ações
    planejador = Planejador()
    agenda = planejador.planejar(
        janelas=resultado_temporal["janelas"],
        modulo=MODULO_ASTROHAIR,
        fuso_offset_h=-3,  # BRT
    )

    # 3. Saída — a tabela que o usuário verá
    print("═══════════════════════════════════════════════════════════════")
    print("KALON ASTRO — Sua Agenda Personalizada")
    print(f"Roberto Gama · AstroHair · Julho 2026")
    print("═══════════════════════════════════════════════════════════════")
    print(f"\n{'DATA':<12} {'HORA':<7} {'JANELA':<14} {'AÇÃO'}")
    print("─" * 75)

    for item in agenda["agenda"]:
        data  = datetime.strptime(item["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
        print(f"{data:<12} {item['hora_pico']:<7} {item['janela']:<14} "
              f"{item['emoji']} {item['acao']}")

    print(f"\nTotal: {agenda['total_acoes']} ações planejadas")

    print("\n\n── RASTRO AUDITÁVEL — PRIMEIRA AÇÃO ──")
    print(json.dumps(agenda["agenda"][0], indent=2, ensure_ascii=False))
