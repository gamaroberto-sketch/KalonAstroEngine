# Knowledge Studio v1.0

**Status:** Ativo  
**Dependências:** Knowledge Repository, Knowledge Loader

## O que é

Ferramenta oficial de análise, validação e saúde da Knowledge Base.  
Não é um produto. É um laboratório de qualidade do conhecimento.

## Comandos

```bash
python knowledge_lab/studio.py coverage     # cobertura da KB
python knowledge_lab/studio.py queue        # fila de calibração
python knowledge_lab/studio.py rules        # distribuição de regras
python knowledge_lab/studio.py conflicts    # detectar inconsistências
python knowledge_lab/studio.py confidence   # estatísticas de confiança
python knowledge_lab/studio.py simulate --date YYYY-MM-DD
python knowledge_lab/studio.py health       # Knowledge Health Score
python knowledge_lab/studio.py observations # resumo do Learning Engine
python knowledge_lab/studio.py snapshot     # gerar snapshot da KB
```

## Knowledge Health Score

Métrica composta 0-100 que mede a qualidade da Knowledge Base:
coverage_score   × 0.30   (cobertura dos eventos possíveis)

conflict_score   × 0.30   (ausência de conflitos)

confidence_score × 0.40   (distribuição de confiança)

| Score | Label |
|---|---|
| ≥ 90 | 🟢 EXCELENTE |
| ≥ 75 | 🟡 BOM |
| ≥ 60 | 🟠 REGULAR |
| < 60 | 🔴 ATENÇÃO |

## Ciclo de Qualidade
Studio (queue) → revela lacunas

↓

SolarFire + Calibrador → preenche lacunas

↓

Studio (coverage) → confirma cobertura

↓

Studio (conflicts) → confirma consistência

↓

Reference App → uso diário

↓

Learning Engine → registra observações

↓

Confidence Updater → evolui confiança

↓

Studio (health) → score melhora

## Estados da Knowledge Base
pending → approved (calibrated.yaml)

pending → rejected (rejected.yaml)

approved → archived (archived.yaml)

archived → approved (restore)

Nenhuma entrada é deletada. Apenas muda de estado.
