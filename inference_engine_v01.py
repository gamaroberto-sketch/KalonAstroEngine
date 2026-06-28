"""
KALON ASTRO — Motor de Inferência v0.1
=======================================
Ontologia: v1.0 (congelada)
Decisões arquiteturais:
  - Entrada: Entidade Astrológica (mapa natal)
  - Saída: estrutura com fontes por convergência
  - Sem pesos, sem interpretação, sem IA
  - Filtrável por contexto/tradição
"""

import yaml
import os
import json
import sys
import io
from typing import Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

GRAPH_ROOT = os.path.join(os.path.dirname(__file__), "knowledge", "graph")

CAMADAS = {
    "planeta":   "planets",
    "signo":     "signs",
    "casa":      "houses",
    "aspecto":   "aspects",
    "dignidade": "dignities",
}

# Grupos de contextos compatíveis por tradição
GRUPOS_CONTEXTO = {
    "ocidental_todas": {
        "ocidental_todas", "ocidental_moderna", "ocidental_medieval",
        "ocidental_helenistica", "ocidental_tradicional",
        "astromedicina_ocidental", "astromedicina_moderna",
        "astromedicina_medieval", "psicologia_arquetipica",
        "astronomico", "astronomico_tropical", "numerologia_pitagorica",
        "historico",
    },
    "vedica": {
        "vedica", "vedica_vimshotari",
    },
}

# Tipos de aresta que produzem convergências, por categoria
TIPOS_CONVERGENCIA = {
    "indicador":       {"influencia_indicador"},
    "dominio":         {"atua_em_dominio", "manifesta_dominio"},
    "regiao":          {"governa_regiao"},
    "arquetipo":       {"arquetipo"},
    "principio":       {"principio"},
    "correspondencia": {
        "corresponde_a_metal", "corresponde_a_cor", "corresponde_a_pedra",
        "corresponde_a_planta", "corresponde_a_dia", "corresponde_a_animal",
    },
}


# ── CARREGAMENTO DO GRAFO ─────────────────────────────────────────────────────

def carregar_no(tipo: str, id_no: str) -> Optional[dict]:
    """Carrega um nó do grafo pelo tipo e id."""
    pasta = os.path.join(GRAPH_ROOT, CAMADAS.get(tipo, tipo))
    if not os.path.isdir(pasta):
        return None
    for arquivo in os.listdir(pasta):
        if not arquivo.endswith(".yaml"):
            continue
        caminho = os.path.join(pasta, arquivo)
        with open(caminho, encoding="utf-8") as f:
            dados = yaml.safe_load(f)
        if dados.get("node", {}).get("id") == id_no:
            return dados
    return None


def arestas_por_contexto(no: dict, contexto: Optional[str] = None) -> list:
    """
    Retorna arestas do nó filtradas por contexto.
    contexto=None retorna todas as arestas.
    Contextos de especialidade (astromedicina, psicologia_arquetipica, etc.)
    são incluídos automaticamente quando o grupo ocidental está ativo.
    """
    relacoes = no.get("relacoes", [])
    if contexto is None:
        return relacoes
    contextos_validos = GRUPOS_CONTEXTO.get(contexto, {contexto})
    return [r for r in relacoes if r.get("contexto") in contextos_validos]


# ── ENTIDADE ASTROLÓGICA ──────────────────────────────────────────────────────

class EntidadeAstrologica:
    """
    Representa um mapa natal ou qualquer entidade astrológica.
    O motor nunca recebe objetos isolados — recebe sempre a entidade completa.

    Cada posição tem:
      objeto    : id do planeta/asteroide/ponto
      signo     : id do signo
      casa      : id da casa
      dignidade : id da dignidade (opcional)
    """

    def __init__(self, nome: str, tipo: str = "mapa_natal"):
        self.nome = nome
        self.tipo = tipo
        self.posicoes: list[dict] = []

    def adicionar_posicao(self, objeto: str, signo: str, casa: str,
                          dignidade: Optional[str] = None):
        self.posicoes.append({
            "objeto":    objeto,
            "signo":     signo,
            "casa":      casa,
            "dignidade": dignidade,
        })

    def __repr__(self):
        return (f"EntidadeAstrologica(nome={self.nome!r}, "
                f"tipo={self.tipo!r}, posicoes={len(self.posicoes)})")


# ── MOTOR DE INFERÊNCIA ───────────────────────────────────────────────────────

class MotorInferencia:
    """
    Motor de Inferência v0.1
    Entrada:  EntidadeAstrologica
    Saída:    estrutura de convergências com fontes
    """

    def __init__(self, contexto: Optional[str] = None):
        self.contexto = contexto

    def analisar(self, entidade: EntidadeAstrologica) -> dict:
        resultado = {
            "entidade": entidade.nome,
            "tipo":     entidade.tipo,
            "contexto": self.contexto or "todos",
            "posicoes_analisadas": len(entidade.posicoes),
            "convergencias": {cat: {} for cat in TIPOS_CONVERGENCIA},
        }
        for posicao in entidade.posicoes:
            self._processar_posicao(posicao, resultado["convergencias"])
        return resultado

    def _processar_posicao(self, posicao: dict, convergencias: dict):
        # Nós a consultar para cada posição
        fontes = [
            ("planeta",   posicao["objeto"]),
            ("signo",     posicao["signo"]),
            ("casa",      posicao["casa"]),
        ]
        if posicao.get("dignidade"):
            fontes.append(("dignidade", posicao["dignidade"]))

        for tipo_no, id_no in fontes:
            no = carregar_no(tipo_no, id_no)
            if no is None:
                continue
            arestas = arestas_por_contexto(no, self.contexto)
            self._extrair_convergencias(arestas, id_no, convergencias)

    def _extrair_convergencias(self, arestas: list, fonte: str,
                               convergencias: dict):
        for aresta in arestas:
            tipo  = aresta.get("tipo", "")
            alvo  = str(aresta.get("alvo", ""))
            for categoria, tipos_validos in TIPOS_CONVERGENCIA.items():
                if tipo in tipos_validos:
                    cat = convergencias[categoria]
                    if alvo not in cat:
                        cat[alvo] = {"fontes": [], "count": 0}
                    if fonte not in cat[alvo]["fontes"]:
                        cat[alvo]["fontes"].append(fonte)
                        cat[alvo]["count"] += 1


# ── FORMATAÇÃO DA SAÍDA ───────────────────────────────────────────────────────

def formatar_resultado(resultado: dict) -> str:
    linhas = [
        "═══════════════════════════════════════════════════",
        "KALON ASTRO — Motor de Inferência v0.1",
        f"Entidade : {resultado['entidade']}",
        f"Tipo     : {resultado['tipo']}",
        f"Contexto : {resultado['contexto']}",
        f"Posições : {resultado['posicoes_analisadas']}",
        "═══════════════════════════════════════════════════",
    ]
    for categoria, itens in resultado["convergencias"].items():
        if not itens:
            continue
        ordenados = sorted(itens.items(), key=lambda x: -x[1]["count"])
        linhas.append(f"\n{categoria.upper()}:")
        for alvo, dados in ordenados:
            fontes_str = ", ".join(dados["fontes"])
            marca = " ◄ TRIPLA" if dados["count"] >= 3 else (
                    " ◄ DUPLA"  if dados["count"] >= 2 else "")
            linhas.append(f"  {alvo}:")
            linhas.append(f"    fontes : [{fontes_str}]{marca}")
    return "\n".join(linhas)


# ── TESTE: MARTE EM ÁRIES NA CASA I ──────────────────────────────────────────

if __name__ == "__main__":
    mapa = EntidadeAstrologica(nome="Mapa Teste", tipo="mapa_natal")
    mapa.adicionar_posicao(
        objeto="marte",
        signo="aries",
        casa="casa_1",
        dignidade="domicilio",
    )

    motor = MotorInferencia(contexto="ocidental_todas")
    resultado = motor.analisar(mapa)

    print(formatar_resultado(resultado))

    print("\n\n── ESTRUTURA BRUTA (para Motor v2) ──")
    print(json.dumps(resultado["convergencias"], indent=2, ensure_ascii=False))
