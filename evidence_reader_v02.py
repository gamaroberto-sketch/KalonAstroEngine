"""
KALON ASTRO — Leitor de Evidências v0.2
========================================
Sprint 2 — Potenciais · Desafios · Fatores de Equilíbrio

Novidades vs v0.1:
  - Lê classificacao dos indicadores (potencial / desafio / duplo)
  - Separa evidências em três perspectivas
  - Identifica fatores de equilíbrio (objetos compartilhados entre perspectivas)
  - Zero pesos, zero probabilidades, zero interpretação clínica
"""

import yaml
import os
import json
from typing import Optional


GRAPH_ROOT = os.path.join(os.path.dirname(__file__), "knowledge")
EVIDENCE_PATH = os.path.join(GRAPH_ROOT, "domains", "astrohair", "evidence")
INDICATORS_PATH = os.path.join(GRAPH_ROOT, "graph", "indicators")


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
        objetos = set()
        for pos in self.posicoes:
            objetos.add(pos["objeto"])
            objetos.add(pos["signo"])
            objetos.add(pos["casa"])
            if pos.get("dignidade"):
                objetos.add(pos["dignidade"])
        return objetos


# ── CARREGADORES ──────────────────────────────────────────────────────────────

def carregar_evidencias(dominio: Optional[str] = None) -> list[dict]:
    evidencias = []
    for f in sorted(os.listdir(EVIDENCE_PATH)):
        if not f.endswith(".yaml"): continue
        with open(os.path.join(EVIDENCE_PATH, f), encoding="utf-8") as fh:
            ev = yaml.safe_load(fh)
        if dominio and dominio not in ev.get("dominios", []):
            continue
        evidencias.append(ev)
    return evidencias

def carregar_classificacoes() -> dict[str, str]:
    """Retorna {id_indicador: classificacao} para todos os indicadores."""
    classif = {}
    for f in os.listdir(INDICATORS_PATH):
        if not f.endswith(".yaml"): continue
        with open(os.path.join(INDICATORS_PATH, f), encoding="utf-8") as fh:
            g = yaml.safe_load(fh)
        node = g.get("node", {})
        if "classificacao" in node:
            classif[node["id"]] = node["classificacao"]
    return classif


# ── LEITOR DE EVIDÊNCIAS v0.2 ─────────────────────────────────────────────────

class LeitorEvidenciasV2:
    """
    Sprint 2 — três perspectivas por mapa:
      potenciais  : evidências que alimentam indicadores favoráveis
      desafios    : evidências que alimentam indicadores de atenção
      equilibrios : objetos que aparecem em ambos os lados
    """

    def ler(self, entidade: EntidadeAstrologica,
             dominio: Optional[str] = None) -> dict:

        objetos_mapa = entidade.extrair_todos_os_objetos()
        evidencias = carregar_evidencias(dominio)
        classificacoes = carregar_classificacoes()

        potenciais = {}
        desafios = {}
        duplos = {}

        for ev in evidencias:
            ev_id = ev["id"]
            objetos_possiveis = ev.get("objetos", [])
            objetos_ativados = [o for o in objetos_possiveis if o in objetos_mapa]
            if not objetos_ativados:
                continue

            posicoes_ativadas = [p for p in ev.get("posicoes_relevantes", [])
                                 if p in objetos_mapa]
            signos_ativados = [s for s in ev.get("signos_relevantes", [])
                               if s in objetos_mapa]

            entrada = {
                "objetos_ativados":          objetos_ativados,
                "posicoes_relevantes_ativas": posicoes_ativadas,
                "signos_relevantes_ativos":   signos_ativados,
                "indicadores":               ev.get("indicadores", []),
                "processos":                 ev.get("processos", []),
            }

            # Classificar via indicadores
            inds = ev.get("indicadores", [])
            classes = {classificacoes.get(i) for i in inds if i in classificacoes}

            tem_potencial = "potencial" in classes
            tem_desafio   = "desafio"   in classes or "duplo" in classes

            if tem_potencial and tem_desafio:
                duplos[ev_id] = entrada
            elif tem_potencial:
                potenciais[ev_id] = entrada
            elif tem_desafio:
                desafios[ev_id] = entrada

        # Fatores de equilíbrio — objetos que aparecem em ambos os lados
        objetos_potencial = set()
        for dados in potenciais.values():
            objetos_potencial.update(dados["objetos_ativados"])

        objetos_desafio = set()
        for dados in desafios.values():
            objetos_desafio.update(dados["objetos_ativados"])

        # Objetos duplos também contribuem para equilíbrio
        for dados in duplos.values():
            objetos_potencial.update(dados["objetos_ativados"])
            objetos_desafio.update(dados["objetos_ativados"])

        fatores_equilibrio = sorted(objetos_potencial & objetos_desafio)

        return {
            "entidade":           entidade.nome,
            "dominio":            dominio or "todos",
            "potenciais":         potenciais,
            "desafios":           desafios,
            "duplos":             duplos,
            "fatores_equilibrio": fatores_equilibrio,
        }


# ── EXPLICADOR TÉCNICO v0.2 ───────────────────────────────────────────────────

class ExplicadorTecnicoV2:

    def explicar(self, leitura: dict) -> str:
        linhas = [
            "═══════════════════════════════════════════════════════════",
            "KALON ASTRO — Leitor de Evidências v0.2",
            f"Entidade : {leitura['entidade']}",
            f"Domínio  : {leitura['dominio']}",
            "═══════════════════════════════════════════════════════════",
        ]

        # ── POTENCIAIS ────────────────────────────────────────────────
        linhas.append("\n◆ POTENCIAIS — o que favorece a saúde capilar")
        linhas.append("─" * 45)
        if leitura["potenciais"]:
            for ev_id, dados in leitura["potenciais"].items():
                linhas += self._formatar_evidencia(ev_id, dados)
        else:
            linhas.append("  (nenhuma evidência de potencial identificada)")

        # ── DESAFIOS ──────────────────────────────────────────────────
        linhas.append("\n◆ DESAFIOS — o que pode exigir atenção")
        linhas.append("─" * 45)
        if leitura["desafios"]:
            for ev_id, dados in leitura["desafios"].items():
                linhas += self._formatar_evidencia(ev_id, dados)
        else:
            linhas.append("  (nenhuma evidência de desafio identificada)")

        # ── DUPLOS ────────────────────────────────────────────────────
        if leitura["duplos"]:
            linhas.append("\n◆ DUPLOS — favorecem e desafiam conforme o contexto")
            linhas.append("─" * 45)
            for ev_id, dados in leitura["duplos"].items():
                linhas += self._formatar_evidencia(ev_id, dados)

        # ── FATORES DE EQUILÍBRIO ─────────────────────────────────────
        linhas.append("\n◆ FATORES DE EQUILÍBRIO")
        linhas.append("─" * 45)
        if leitura["fatores_equilibrio"]:
            linhas.append("  Objetos presentes em ambos os lados:")
            for obj in leitura["fatores_equilibrio"]:
                linhas.append(f"    - {obj}")
        else:
            linhas.append("  (nenhum fator de equilíbrio identificado)")

        return "\n".join(linhas)

    def _formatar_evidencia(self, ev_id: str, dados: dict) -> list[str]:
        linhas = [f"\n  Evidência: {ev_id}"]
        linhas.append(f"    Ativada por: {', '.join(dados['objetos_ativados'])}")
        if dados["posicoes_relevantes_ativas"]:
            linhas.append(f"    Posições: {', '.join(dados['posicoes_relevantes_ativas'])}")
        if dados["signos_relevantes_ativos"]:
            linhas.append(f"    Signos: {', '.join(dados['signos_relevantes_ativos'])}")
        linhas.append(f"    Indicadores: {', '.join(dados['indicadores'])}")
        linhas.append(f"    Via processo: {', '.join(dados['processos'])}")
        return linhas


# ── TESTE: MAPA DE ROBERTO GAMA ──────────────────────────────────────────────

if __name__ == "__main__":
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

    leitor = LeitorEvidenciasV2()
    leitura = leitor.ler(mapa, dominio="astrohair")

    explicador = ExplicadorTecnicoV2()
    print(explicador.explicar(leitura))
