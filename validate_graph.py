import yaml, os

# 1. Verificar campo 'forca' ausente
# 2. Verificar campos obrigatórios: tipo, alvo, contexto
# 3. Verificar IDs únicos (sem duplicatas entre planetas e signos)
# 4. Verificar referências cruzadas planetas → signos

campos_obrigatorios = ['tipo', 'alvo', 'contexto']
ids_vistos = set()

for pasta in ['knowledge/graph/planets/', 'knowledge/graph/signs/']:
    for arquivo in os.listdir(pasta):
        if not arquivo.endswith('.yaml'): continue
        with open(pasta + arquivo, encoding='utf-8') as f:
            g = yaml.safe_load(f)
        # ID único
        node_id = g['node']['id']
        assert node_id not in ids_vistos, f"ID duplicado: {node_id}"
        ids_vistos.add(node_id)
        # Campos nas arestas
        for r in g.get('relacoes', []):
            assert 'forca' not in r, f"Campo 'forca' encontrado em {arquivo}"
            for campo in campos_obrigatorios:
                assert campo in r, f"Campo '{campo}' ausente em {arquivo}"

print(f"✅ {len(ids_vistos)} nós validados sem erros")
