import os, yaml, ast, re, unicodedata

os.makedirs('config/geocoding', exist_ok=True)

with open('kalon_astro_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'CIDADES = (\{.*?\})', content, re.DOTALL)
cidades_dict = ast.literal_eval(match.group(1))

cidades_yaml = {"versao": "1.0", "cidades": {}}

def slug(text):
    text = text.split(',')[0].strip()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8').lower()
    return text.replace(' ', '_')

def cap(text):
    return text.split(',')[0].strip().title()

for k, (lat, lon, fuso) in cidades_dict.items():
    s = slug(k)
    estado = k.split(',')[1].strip().upper()
    cidades_yaml['cidades'][s] = {
        "nome": cap(k),
        "estado": estado,
        "pais": "BR",
        "latitude": lat,
        "longitude": lon,
        "utc_offset": f"-0{abs(fuso)}:00" if fuso < 0 else f"+0{fuso}:00"
    }

with open('config/geocoding/cidades_br.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(cidades_yaml, f, sort_keys=False, allow_unicode=True)
