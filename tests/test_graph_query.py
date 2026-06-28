import yaml
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = {
    'MARTE': 'knowledge/graph/planets/mars.yaml',
    'ÁRIES': 'knowledge/graph/signs/aries.yaml',
    'CASA I': 'knowledge/graph/houses/house_01.yaml'
}

data = {}
for name, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        data[name] = yaml.safe_load(f)

target_ids = {data[name]['node']['id'] for name in data}
convergences = []

for name, node_data in data.items():
    print(f"\n{name}")
    node_id = node_data['node']['id']
    
    for rel in node_data.get('relacoes', []):
        tipo = rel.get('tipo', '')
        alvo = rel.get('alvo', '')
        contexto = rel.get('contexto', '')
        
        print(f"  {tipo} -> {alvo} [{contexto}]")
        
        if alvo in target_ids:
            convergences.append(f"  {node_id}.{tipo} -> {alvo}")

print("\nCONVERGÊNCIAS (arestas que conectam os três):")
for conv in convergences:
    print(conv)
