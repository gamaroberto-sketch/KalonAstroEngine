import os, yaml
import copy

os.makedirs('tests/validator/valid', exist_ok=True)
os.makedirs('tests/validator/invalid', exist_ok=True)
os.makedirs('tests/validator/warnings', exist_ok=True)

with open('knowledge/strategies/hair/corte.yaml', 'r', encoding='utf-8') as f:
    corte = yaml.safe_load(f)

with open('knowledge/strategies/diet/metabolico.yaml', 'r', encoding='utf-8') as f:
    diet = yaml.safe_load(f)

def dump_yaml(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

dump_yaml(corte, 'tests/validator/valid/hair_corte.yaml')
dump_yaml(diet, 'tests/validator/valid/diet_metabolico.yaml')

t = copy.deepcopy(corte)
t['calculo']['estrategias']['crescimento']['aspectos'] = {'aspecto_invalido': 45}
dump_yaml(t, 'tests/validator/invalid/unknown_aspect.yaml')

t = copy.deepcopy(corte)
t['calculo']['estrategias']['crescimento']['alvo_natal'] = 'netuno_classico'
dump_yaml(t, 'tests/validator/invalid/unknown_target.yaml')

t = {
  'id': 'test_schema_invalido',
  'tipo': 'calendario_temporal',
  'suite': 'kalon_astro',
  'modulo': 'astrohair',
  'nome': 'Teste Schema Inválido',
  'versao': '1.0.0',
  'calculo': {
    'estrategias': {
      'teste': {
        'alvo_natal': 'sol',
        'aspectos': {'conjuncao': 0},
        'janela_h': 6
      }
    }
  },
  'apresentacao': {
    'teste': {
      'label': 'teste',
      'icones': {'conjuncao': '★'},
      'cores': {'conjuncao': 'gold'},
      'prioridades': {'conjuncao': 'alta'}
    }
  }
}
dump_yaml(t, 'tests/validator/invalid/invalid_schema.yaml')

t = copy.deepcopy(corte)
t['apresentacao']['crescimento']['icones'].pop('sextil', None)
dump_yaml(t, 'tests/validator/invalid/invalid_presentation.yaml')

t = copy.deepcopy(corte)
t['engine']['versao_minima'] = "99.0.0"
dump_yaml(t, 'tests/validator/invalid/incompatible_engine.yaml')

t = copy.deepcopy(corte)
t['calculo']['estrategias']['crescimento']['alvo_natal'] = 'urano'
dump_yaml(t, 'tests/validator/warnings/urano_not_implemented.yaml')

t = copy.deepcopy(corte)
t['calculo']['estrategias']['crescimento']['alvo_natal'] = 'netuno'
dump_yaml(t, 'tests/validator/warnings/netuno_not_implemented.yaml')

t = copy.deepcopy(corte)
t['calculo']['estrategias']['crescimento']['alvo_natal'] = 'plutao'
dump_yaml(t, 'tests/validator/warnings/plutao_not_implemented.yaml')
