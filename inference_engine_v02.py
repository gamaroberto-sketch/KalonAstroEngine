"""
KALON ASTRO — Motor de Inferência v0.2
=======================================
Ontologia: v1.0 (congelada)
Quatro operações permitidas: Navegar / Filtrar / Agrupar / Explicar
PROIBIDO: inferir, pontuar, priorizar, interpretar, decidir

Novidades vs v0.1:
  - Navega a camada fisiológica (determinado_por_processo)
  - Conecta processos a objetos astrológicos (relacionado_a_objeto)
  - Lê domínios especializados (pertence_a_dominio)
  - Saída em árvore auditável com rastro completo
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
    "planeta":    "planets",
    "signo":      "signs",
    "casa":       "houses",
    "aspecto":    "aspects",
    "dignidade":  "dignities",
    "ponto":      "points",
    "dominio":    "body_systems",
    "anatomia":   "anatomy",
    "fisiologia": "physiology",
    "indicador":  "indicators",
}

GRUPOS_CONTEXTO = {
    "ocidental_todas": {
        "ocidental_todas", "ocidental_moderna", "ocidental_medieval",
        "ocidental_helenistica", "ocidental_tradicional",
        "astromedicina_ocidental", "astromedicina_moderna",
        "astromedicina_medieval", "psicologia_arquetipica",
        "astronomico", "astronomico_tropical", "numerologia_pitagorica",
        "historico", "fisiologia_universal", "anatomia_universal",
        "saude_capilar",
    },
    "vedica": {
        "vedica", "vedica_vimshotari",
    },
}

# ── ÍNDICE DO GRAFO (carrega tudo uma vez) ────────────────────────────────────

_INDICE: dict[str, dict] = {}

def _construir_indice():
    """Carrega todos os nós do grafo em memória."""
    global _INDICE
    if _INDICE:
        return
    for tipo, pasta_rel in CAMADAS.items():
        pasta = os.path.join(GRAPH_ROOT, pasta_rel)
        if not os.path.isdir(pasta):
            continue
        for arquivo in os.listdir(pasta):
            if not arquivo.endswith(".yaml"):
                continue
            with open(os.path.join(pasta, arquivo), encoding="utf-8") as f:
                dados = yaml.safe_load(f)
            node_id = dados.get("node", {}).get("id")
            if node_id:
                _INDICE[node_id] = dados

def buscar_no(id_no: str) -> Optional[dict]:
    _construir_indice()
    return _INDICE.get(id_no)

def arestas_filtradas(no: dict, contexto: Optional[str], tipos: set) -> list:
    """Filtra arestas por contexto e tipos permitidos."""
    contextos_validos = GRUPOS_CONTEXTO.get(contexto, {contexto}) if contexto else None
    resultado = []
    for r in no.get("relacoes", []):
        if r.get("tipo") not in tipos:
            continue
        if contextos_validos and r.get("contexto") not in contextos_validos:
            continue
        resultado.append(r)
    return resultado


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


# ── MOTOR v0.2 ────────────────────────────────────────────────────────────────

class MotorInferencia:
    """
    Motor de Inferência v0.2
    Operações: Navegar / Filtrar / Agrupar / Explicar
    """

    # Tipos de aresta que o motor pode percorrer
    TIPOS_OBJETO_PARA_PROCESSO = {
        "relacionado_a_objeto",   # processo → objeto astrológico
        "relacionado_a_signo",
        "relacionado_a_casa",
    }

    TIPOS_PROCESSO_PARA_INDICADOR = {
        "determinado_por_processo",  # indicador → processo
        "pode_causar",               # processo → indicador
    }

    TIPOS_INDICADOR_PARA_DOMINIO = {
        "pertence_a_dominio",        # indicador → domínio
    }

    def __init__(self, contexto: Optional[str] = None):
        self.contexto = contexto

    def analisar_dominio(self, entidade: EntidadeAstrologica,
                         dominio_alvo: str) -> dict:
        """
        Navega o grafo a partir da entidade e retorna
        todos os indicadores do domínio com rastro auditável.

        Saída:
        {
          "entidade": str,
          "dominio": str,
          "indicadores": {
            "queda_capilar": {
              "processos": {
                "inflamacao": {
                  "objetos": ["marte", "escorpiao", "casa_6"],
                  "fontes_na_entidade": ["marte", "escorpiao"]
                }
              }
            }
          }
        }
        """
        _construir_indice()

        # 1. NAVEGAR — encontrar todos os indicadores do domínio
        indicadores_do_dominio = self._encontrar_indicadores(dominio_alvo)

        # 2. NAVEGAR — para cada indicador, encontrar os processos
        resultado = {
            "entidade": entidade.nome,
            "dominio":  dominio_alvo,
            "contexto": self.contexto or "todos",
            "indicadores": {},
        }

        objetos_da_entidade = self._extrair_objetos(entidade)

        for id_indicador in indicadores_do_dominio:
            no_ind = buscar_no(id_indicador)
            if not no_ind:
                continue

            # 3. NAVEGAR — processos que determinam este indicador
            processos = self._encontrar_processos(no_ind)

            if not processos:
                continue

            entrada_indicador = {"processos": {}}

            for id_processo in processos:
                no_proc = buscar_no(id_processo)
                if not no_proc:
                    continue

                # 4. NAVEGAR — objetos astrológicos ligados ao processo
                objetos_do_processo = self._encontrar_objetos_do_processo(no_proc)

                # 5. FILTRAR — quais desses objetos estão na entidade
                presentes = [o for o in objetos_do_processo
                             if o in objetos_da_entidade]

                if not presentes:
                    continue

                # 6. AGRUPAR — registrar com rastro
                entrada_indicador["processos"][id_processo] = {
                    "objetos_no_grafo":    sorted(objetos_do_processo),
                    "objetos_na_entidade": sorted(presentes),
                }

            if entrada_indicador["processos"]:
                resultado["indicadores"][id_indicador] = entrada_indicador

        return resultado

    # ── MÉTODOS DE NAVEGAÇÃO ──────────────────────────────────────────────

    def _encontrar_indicadores(self, dominio_alvo: str) -> list[str]:
        """Encontra todos os indicadores que pertencem a um domínio."""
        ids = []
        for id_no, dados in _INDICE.items():
            if dados.get("node", {}).get("tipo") != "indicador":
                continue
            for r in dados.get("relacoes", []):
                if (r.get("tipo") == "pertence_a_dominio"
                        and r.get("alvo") == dominio_alvo):
                    ids.append(id_no)
                    break
        return ids

    def _encontrar_processos(self, no_indicador: dict) -> list[str]:
        """Encontra processos fisiológicos que determinam um indicador."""
        arestas = arestas_filtradas(
            no_indicador, self.contexto,
            {"determinado_por_processo"}
        )
        return [r["alvo"] for r in arestas]

    def _encontrar_objetos_do_processo(self, no_processo: dict) -> list[str]:
        """Encontra objetos astrológicos relacionados a um processo."""
        arestas = arestas_filtradas(
            no_processo, self.contexto,
            {"relacionado_a_objeto", "relacionado_a_signo", "relacionado_a_casa"}
        )
        return [r["alvo"] for r in arestas]

    def _extrair_objetos(self, entidade: EntidadeAstrologica) -> set[str]:
        """Extrai todos os objetos presentes na entidade."""
        objetos = set()
        for pos in entidade.posicoes:
            objetos.add(pos["objeto"])
            objetos.add(pos["signo"])
            objetos.add(pos["casa"])
            if pos.get("dignidade"):
                objetos.add(pos["dignidade"])
        return objetos


# ── FORMATAÇÃO EM ÁRVORE AUDITÁVEL ───────────────────────────────────────────

def formatar_arvore(resultado: dict) -> str:
    """
    Formata a saída como árvore auditável com rastro completo.

    Saúde Capilar
    ├── queda_capilar
    │   ├── inflamacao
    │   │   └── objetos na entidade: marte, escorpiao
    │   └── regulacao_hormonal
    │       └── objetos na entidade: lua, saturno
    """
    linhas = [
        "═══════════════════════════════════════════════════════════",
        f"KALON ASTRO — Motor v0.2 | {resultado['dominio']}",
        f"Entidade : {resultado['entidade']}",
        f"Contexto : {resultado['contexto']}",
        "═══════════════════════════════════════════════════════════",
        f"\n{resultado['dominio']}",
    ]

    indicadores = resultado["indicadores"]
    ids_ind = sorted(indicadores.keys())
    for i, id_ind in enumerate(ids_ind):
        eh_ultimo_ind = (i == len(ids_ind) - 1)
        prefixo_ind = "└──" if eh_ultimo_ind else "├──"
        continua_ind = "    " if eh_ultimo_ind else "│   "

        linhas.append(f"{prefixo_ind} {id_ind}")

        processos = indicadores[id_ind]["processos"]
        ids_proc = sorted(processos.keys())
        for j, id_proc in enumerate(ids_proc):
            eh_ultimo_proc = (j == len(ids_proc) - 1)
            prefixo_proc = "└──" if eh_ultimo_proc else "├──"
            continua_proc = "    " if eh_ultimo_proc else "│   "

            linhas.append(f"{continua_ind}{prefixo_proc} {id_proc}")

            objetos = processos[id_proc]["objetos_na_entidade"]
            for k, obj in enumerate(objetos):
                eh_ultimo_obj = (k == len(objetos) - 1)
                prefixo_obj = "└──" if eh_ultimo_obj else "├──"
                linhas.append(f"{continua_ind}{continua_proc}{prefixo_obj} {obj}")

    return "\n".join(linhas)


# ── TESTE: MAPA DE ROBERTO GAMA — DOMÍNIO SAÚDE CAPILAR ─────────────────────

if __name__ == "__main__":
    mapa = EntidadeAstrologica(nome="Roberto Gama", tipo="mapa_natal")

    # Posições calculadas via pyswisseph (29/08/1957 00:00 BZT / Ourinhos-SP)
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

    motor = MotorInferencia(contexto="ocidental_todas")
    resultado = motor.analisar_dominio(mapa, dominio_alvo="saude_capilar")

    # Saída em árvore
    print(formatar_arvore(resultado))

    # Estrutura bruta para auditoria
    print("\n\n── RASTRO COMPLETO (JSON) ──")
    print(json.dumps(resultado["indicadores"], indent=2, ensure_ascii=False))
