# Kalon Astro Engine — Constituição v2.0
**Data:** 2026-06-26  
**Status:** Foundation Freeze — ecosystem-v1.0

---

## 1. O que é o Kalon Astro Engine?

O Kalon Astro Engine é uma plataforma de conhecimento astrológico que combina 
cálculo astronômico preciso, base de conhecimento calibrada e aprendizado 
contínuo com base em evidências observacionais.

Não é um software de horóscopo.  
Não é um gerador de relatórios.  
É uma plataforma onde o conhecimento evolui de forma controlada, auditável 
e reversível — orientada por dados e validada pela experiência humana.

---

## 2. Componentes

| Componente | Responsabilidade |
|---|---|
| **Core Engine** | Cálculo astronômico preciso via Swiss Ephemeris. Congelado. |
| **Aspect Engine** | Detecção de aspectos entre objetos astrológicos. Congelado. |
| **Query Engine** | Interface semântica de consulta ao Core. |
| **Timeline Engine** | Geração de cronologia de eventos astronômicos. |
| **Knowledge Engine** | Execução de pacotes de conhecimento YAML contra eventos. |
| **Knowledge Studio** | Ferramenta de análise, validação e saúde da Knowledge Base. |
| **Reference App** | Aplicação de referência interna para validação diária. |
| **Learning Engine** | Registro imutável de observações e atualização de confiança. |
| **Knowledge Repository** | Única camada com permissão de escrita na Knowledge Base. |

---

## 3. O Ciclo Completo
Core Engine

↓  calcula posições e aspectos

Aspect Engine

↓  detecta aspectos

Timeline Engine

↓  gera cronologia de eventos

Knowledge Engine

↓  executa conhecimento contra eventos

Reference App

↓  apresenta recomendação do dia

↓  Roberto observa e compara com SolarFire

Learning Engine

↓  registra observação (imutável)

Confidence Updater

↓  calcula delta via confidence_model.yaml versionado

Knowledge Repository

↓  atualiza confiança + registra no journal

Knowledge Studio

↓  mede cobertura, conflitos, health score

↓  revela lacunas e prioridades

Knowledge Base

↓  evolui com evidências reais

(ciclo reinicia)

---

## 4. Princípios Fundamentais

1. **Nunca perder conhecimento.** Nenhuma entrada é deletada — apenas muda de estado.

2. **Evidência antes de confiança.** Nenhuma confiança é alterada sem observações reais que a sustentem.

3. **Observações são imutáveis.** Fatos registrados nunca são editados. Motores calculam consequências.

4. **O Learning Engine nunca altera conhecimento diretamente.** Toda alteração passa pelo Knowledge Repository.

5. **O Core permanece congelado.** Correções de bugs são permitidas; mudanças estruturais não.

6. **O conhecimento evolui; o motor permanece estável.** Novos produtos são novos pacotes YAML, não novos motores.

7. **Separação absoluta de responsabilidades.** Loader lê. Validator valida. Journal registra. Repository escreve. Nenhum cruza fronteiras.

8. **Rastreabilidade total.** Toda alteração tem autor, data, motivo e estado anterior preservado.

---

## 5. Estados da Knowledge Base
pending → approved → archived

pending → rejected

rejected → pending (restore)

Nenhum estado é final exceto `rejected` sem restauração explícita.

---

## 6. Produtos do Ecossistema

O mesmo ciclo será reutilizado em todos os produtos Kalon:

| Produto | Domínio | Status |
|---|---|---|
| AstroHair | Cuidados capilares | Em validação |
| AstroDiet | Nutrição e metabolismo | Aguarda maturidade do AstroHair |
| AstroCash | Finanças e investimentos | Planejado |
| AstroLove | Relacionamentos | Planejado |

Cada produto é um pacote `knowledge/` independente.  
O motor é compartilhado. O conhecimento é específico.
