"""
KALON ASTRO — Leitor de Evidências v0.1 + Explicador Técnico
=============================================================
Sprint 1 — AstroHair MVP

Operações:
  1. Leitor de Evidências: cruza mapa × biblioteca evidence/
  2. Explicador Técnico: descreve cada evidência ativa com rastro

Proibido: ranking, pesos, probabilidade, priorização, texto para usuário
"""

import yaml
import os
import json
from typing import Optional


# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

GRAPH_ROOT = os.path.join(os.path.dirname(__file__), "knowledge")
EVIDENCE_PATH = os.path.join(GRAPH_ROOT, "domains", "astrohair", "evidence")


# ── ENTIDADE ASTROLÓGICA ──────────────────────────────────────────────────────

class EntidadeAstrologica:
    def __init__(self, nome: str, tipo: str = "mapa_natal"):
        self.nome = nome
        self.tipo = tipo
        self.posicoes: list[dict] = []

    def adicionar_posicao(self, objeto: str, signo: str, casa: str,
                          dignidade: Optional[str] = None):
        self.posicoes.append({
            "objeto": objeto, "signo": signo,
            "casa": casa, "dignidade": dignidade,
        })

    def extrair_todos_os_objetos(self) -> set[str]:
        """Retorna todos os IDs presentes no mapa."""
        objetos = set()
        for pos in self.posicoes:
            objetos.add(pos["objeto"])
            objetos.add(pos["signo"])
            objetos.add(pos["casa"])
            if pos.get("dignidade"):
                objetos.add(pos["dignidade"])
        return objetos


# ── LEITOR DE EVIDÊNCIAS ──────────────────────────────────────────────────────

class LeitorEvidencias:
    """
    Item 1 do Sprint 1.
    Cruza o mapa da entidade com a biblioteca evidence/.
    Retorna evidências ativas com rastro auditável.
    """

    def __init__(self, caminho_evidencias: str = EVIDENCE_PATH):
        self.caminho = caminho_evidencias
        self._evidencias: list[dict] = []
        self._carregar()

    def _carregar(self):
        """Carrega todos os arquivos de evidência."""
        for arquivo in sorted(os.listdir(self.caminho)):
            if not arquivo.endswith(".yaml"):
                continue
            with open(os.path.join(self.caminho, arquivo), encoding="utf-8") as f:
                self._evidencias.append(yaml.safe_load(f))

    def ler(self, entidade: EntidadeAstrologica,
             dominio: Optional[str] = None) -> dict:
        """
        Cruza a entidade com a biblioteca de evidências.

        Saída:
        {
          "entidade": str,
          "dominio_filtro": str,
          "evidencias_ativas": {
            "inflamacao": {
              "objetos_possiveis": ["marte", "escorpiao"],
              "objetos_ativados": ["marte", "escorpiao"],
              "posicoes_relevantes_possiveis": ["casa_1", "casa_6"],
              "posicoes_relevantes_ativadas": [],
              "signos_relevantes_possiveis": [],
              "signos_relevantes_ativados": [],
              "indicadores": ["queda_capilar", "inflamacao_capilar"],
              "processos": ["inflamacao"],
              "dominios": ["astrohair", ...]
            }
          },
          "evidencias_inativas": ["hidratacao", ...]
        }
        """
        objetos_mapa = entidade.extrair_todos_os_objetos()

        ativas = {}
        inativas = []

        for ev in self._evidencias:
            ev_id = ev.get("id")

            # Filtrar por domínio se especificado
            if dominio and dominio not in ev.get("dominios", []):
                continue

            # Objetos principais
            objetos_possiveis = ev.get("objetos", [])
            objetos_ativados = [o for o in objetos_possiveis if o in objetos_mapa]

            # Posições relevantes
            posicoes_possiveis = ev.get("posicoes_relevantes", [])
            posicoes_ativadas = [p for p in posicoes_possiveis if p in objetos_mapa]

            # Signos relevantes
            signos_possiveis = ev.get("signos_relevantes", [])
            signos_ativados = [s for s in signos_possiveis if s in objetos_mapa]

            # Evidência ativa se ao menos 1 objeto principal está no mapa
            if objetos_ativados:
                ativas[ev_id] = {
                    "objetos_possiveis":            objetos_possiveis,
                    "objetos_ativados":             objetos_ativados,
                    "posicoes_relevantes_possiveis": posicoes_possiveis,
                    "posicoes_relevantes_ativadas":  posicoes_ativadas,
                    "signos_relevantes_possiveis":   signos_possiveis,
                    "signos_relevantes_ativados":    signos_ativados,
                    "indicadores":                  ev.get("indicadores", []),
                    "processos":                    ev.get("processos", []),
                    "dominios":                     ev.get("dominios", []),
                }
            else:
                inativas.append(ev_id)

        return {
            "entidade":          entidade.nome,
            "dominio_filtro":    dominio or "todos",
            "total_ativas":      len(ativas),
            "total_inativas":    len(inativas),
            "evidencias_ativas": ativas,
            "evidencias_inativas": inativas,
        }


# ── EXPLICADOR TÉCNICO ────────────────────────────────────────────────────────

class ExplicadorTecnico:
    """
    Item 2 do Sprint 1.
    Formata cada evidência ativa em linguagem técnica estruturada.
    Sem interpretação. Sem aconselhamento. Sem linguagem comercial.
    """

    def explicar(self, leitura: dict) -> str:
        linhas = [
            "═══════════════════════════════════════════════════════════",
            f"KALON ASTRO — Leitor de Evidências v0.1",
            f"Entidade : {leitura['entidade']}",
            f"Domínio  : {leitura['dominio_filtro']}",
            f"Ativas   : {leitura['total_ativas']} | "
            f"Inativas : {leitura['total_inativas']}",
            "═══════════════════════════════════════════════════════════",
        ]

        for ev_id, dados in leitura["evidencias_ativas"].items():
            linhas.append(f"\nEvidência: {ev_id}")
            linhas.append(f"{'─' * 45}")

            # Objetos que ativaram
            linhas.append(f"  Ativada por (objetos):")
            for obj in dados["objetos_ativados"]:
                linhas.append(f"    - {obj}")

            # Posições relevantes presentes
            if dados["posicoes_relevantes_ativadas"]:
                linhas.append(f"  Posições relevantes presentes:")
                for pos in dados["posicoes_relevantes_ativadas"]:
                    linhas.append(f"    - {pos}")

            # Signos relevantes presentes
            if dados["signos_relevantes_ativados"]:
                linhas.append(f"  Signos relevantes presentes:")
                for sig in dados["signos_relevantes_ativados"]:
                    linhas.append(f"    - {sig}")

            # Objetos possíveis não presentes
            ausentes = [o for o in dados["objetos_possiveis"]
                       if o not in dados["objetos_ativados"]]
            if ausentes:
                linhas.append(f"  Objetos possíveis não presentes: "
                              f"{', '.join(ausentes)}")

            # Indicadores relacionados
            linhas.append(f"  Relacionada aos indicadores:")
            for ind in dados["indicadores"]:
                linhas.append(f"    - {ind}")

            # Processos fisiológicos
            linhas.append(f"  Via processo fisiológico:")
            for proc in dados["processos"]:
                linhas.append(f"    - {proc}")

            # Domínios de aplicação
            linhas.append(f"  Domínios: {', '.join(dados['dominios'])}")

        # Evidências inativas
        if leitura["evidencias_inativas"]:
            linhas.append(f"\n{'─' * 45}")
            linhas.append(f"Evidências não ativadas neste mapa:")
            for ev_id in leitura["evidencias_inativas"]:
                linhas.append(f"  - {ev_id}")

        return "\n".join(linhas)


# ── TESTE: MAPA DE ROBERTO GAMA ──────────────────────────────────────────────

if __name__ == "__main__":
    # Mapa calculado via pyswisseph — 29/08/1957 00:00 BZT / Ourinhos-SP
    mapa = EntidadeAstrologica(nome="Roberto Gama", tipo="mapa_natal")

    mapa.adicionar_posicao(objeto="sol",      signo="virgem",    casa="casa_4")
    mapa.adicionar_posicao(objeto="lua",      signo="libra",     casa="casa_5")
    mapa.adicionar_posicao(objeto="mercurio", signo="virgem",    casa="casa_4")
    mapa.adicionar_posicao(objeto="venus",    signo="libra",     casa="casa_5")
    mapa.adicionar_posicao(objeto="marte",    signo="virgem",    casa="casa_4")
    mapa.adicionar_posicao(objeto="jupiter",  signo="libra",     casa="casa_5")
    mapa.adicionar_posicao(objeto="saturno",  signo="sagitario", casa="casa_7")
    mapa.adicionar_posicao(objeto="urano",    signo="leao",      casa="casa_3")
    mapa.adicionar_posicao(objeto="netuno",   signo="escorpiao", casa="casa_5")
    mapa.adicionar_posicao(objeto="plutao",   signo="virgem",    casa="casa_4")
    mapa.adicionar_posicao(objeto="asc",      signo="touro",     casa="casa_1")
    mapa.adicionar_posicao(objeto="mc",       signo="peixes",    casa="casa_10")

    # 1. LEITOR DE EVIDÊNCIAS
    leitor = LeitorEvidencias()
    leitura = leitor.ler(mapa, dominio="astrohair")

    # 2. EXPLICADOR TÉCNICO
    explicador = ExplicadorTecnico()
    print(explicador.explicar(leitura))

    # Rastro JSON completo
    print("\n\n── RASTRO AUDITÁVEL (JSON) ──")
    print(json.dumps(leitura, indent=2, ensure_ascii=False))
