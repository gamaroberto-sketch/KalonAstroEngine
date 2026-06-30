# Agenda Kalon

Componente oficial reutilizável do ecossistema Kalon Astro.

## Responsabilidades
✔ Renderizar agenda temporal a partir de uma estratégia
✔ Expandir auditoria de cálculo
✔ Imprimir / PDF / PNG
✔ Múltiplas instâncias na mesma página

## Não faz
✘ Calcular astrologia
✘ Interpretar resultados
✘ Escolher estratégias
✘ Traduzir conhecimento (vem pronto da API)

## Uso
```javascript
const agenda = new AgendaKalon('#meuContainer');
agenda.render({ estrategia: 'hair_corte', nome, data_nascimento, ... });
```

## Contrato com a API
Espera de `POST /api/v1/agenda`: campos com `icone` (glifo pronto), `cor`, `label` (já traduzido), `auditoria` (lista de grupos com `titulo`/`itens`).
