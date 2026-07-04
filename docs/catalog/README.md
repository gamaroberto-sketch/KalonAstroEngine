# Catálogo Oficial de Estratégias — Kalon Astro

## Matriz de Compatibilidade

| Módulo | Origem | Compat. Validada | Desvio Máx. | Diferenças Conhecidas | Motivo |
|--------|--------|-----------------|-------------|----------------------|--------|
| AstroHair (hair_corte) | Gê/Solar Fire | ✅ | 3 min | Nenhuma | — |
| AstroDiet (diet_metabolico) | Gê/Solar Fire | ✅ | 5 min | Nenhuma | — |
| AstroCash Kalon (cash_decisoes_kalon) | Kalon Original | N/A | N/A | Metodologia própria | Produto independente |
| AstroCash Gê (cash_decisoes_ge) | Gê/Solar Fire | ✅ parcial | 5 min | Plutão, midpoints natais | Aguardam implementação |

## Pendências Conhecidas

| Pendência | Afeta | Missão |
|-----------|-------|--------|
| Plutão/Urano/Netuno natais | cash_decisoes_ge | AstroCore — transpessoais |
| Midpoints natais (Ven/Jup natal, Mar/Jup natal) | cash_decisoes_ge | AstroCore-05 |

## Estratégias Planejadas

| ID | Produto | Status |
|----|---------|--------|
| astrolove_ge | AstroLove (Gê) | Planejado |
| astropower_ge | AstroPower (Gê) | Planejado |
| astrostudy_ge | AstroStudy (Gê) | Planejado |

## Decisões Arquiteturais (ADR)

### Precisão do Engine (Moshier vs Swiss Ephemeris)

Kalon Astro Alpha opera em modo Moshier (fallback analítico do pyswisseph) por decisão consciente — precisão validada empiricamente (desvio máx. 5 min vs. Solar Fire) tanto localmente quanto em produção, ambiente idêntico desde o início. Upgrade para efemérides Swiss Ephemeris file-based (`.se1`) fica condicionado a demanda real de precisão identificada durante validação com astrólogos reais (etapa 8 do plano Alpha).
