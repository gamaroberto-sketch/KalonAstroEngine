# Scenario — Foundation Draft
**Status:** Draft (não implementar ainda)
**Data:** 2026-07-01
**Origem:** Decisão da Supervisora, sessão de encerramento da Foundation Phase

## Conceito

O Scenario é um nível arquitetural entre Strategy e Report:
Engine → Strategy → Scenario → Report

## Problema que resolve

Hoje o AstroHair tem apenas um produto: Calendário de Corte.

Amanhã existirão múltiplos produtos dentro do mesmo módulo:
- Calendário de Corte
- Calendário de Tintura
- Calendário de Implante
- Calendário de Hidratação
- Calendário de Reconstrução
- Calendário de Escova

Todos reutilizam as mesmas estratégias (hair_corte e variações), mas
montam experiências diferentes para o usuário final.

## O que é um Scenario

Um Scenario é quem monta experiências diferentes reutilizando as mesmas
estratégias. Ele sabe:
- quais estratégias usar
- como combinar os resultados
- qual layout de Report apresentar
- qual contexto dar ao usuário

## O que NÃO é um Scenario

- Não é uma Strategy (não define cálculo)
- Não é um Report (não renderiza dados)
- Não é um módulo (não é um produto completo)

## Impacto esperado

Quando implementado, o Scenario vai multiplicar o reaproveitamento do
Engine: as mesmas estratégias astrológicas servirão dezenas de produtos
diferentes sem duplicação de cálculo.

## Próximos passos (quando chegar a hora)

1. Definir o schema de um Scenario (similar ao estrategia.schema.yaml)
2. Criar o Scenario Builder (extensão do Strategy Builder)
3. Migrar AstroHair para usar Scenarios
4. Validar com AstroDiet antes de expandir

## Regra de bloqueio

NÃO implementar antes de:
- AstroCash, AstroLove e AstroPower estarem maduros
- O Strategy Builder estar em uso real
- A necessidade de múltiplos Scenarios por módulo ser confirmada empiricamente

---
*Este documento é um Foundation Draft — existe para preservar a decisão
arquitetural, não para guiar implementação imediata.*
