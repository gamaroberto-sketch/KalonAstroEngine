"""
Kalon Astro Engine — Astro Doctor
Diagnóstico completo do sistema. Execute antes de qualquer deploy ou alteração no Core.
"""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OK = "\033[92mOK\033[0m"
FAIL = "\033[91mFAIL\033[0m"

results = []


def check(label, fn):
    try:
        ok, detail = fn()
        status = OK if ok else FAIL
        results.append(ok)
        suffix = f"  ({detail})" if detail else ""
        print(f"  {label:<35} {status}{suffix}")
        return ok
    except Exception as e:
        results.append(False)
        print(f"  {label:<35} {FAIL}  (exception: {e})")
        return False


print()
print("  ╔══════════════════════════════════════════╗")
print("  ║     Kalon Astro Engine — Astro Doctor    ║")
print("  ╚══════════════════════════════════════════╝")
print()

from core.astro_engine import calculate_chart
from core.aspect_engine import detect_aspects, objects_from_chart

CHART_ROBERTO = dict(
    year=1957, month=8, day=29,
    hour=0, minute=0,
    latitude=-(22 + 59/60),
    longitude=-(49 + 52/60),
    timezone_offset=-3.0
)

# ─── Swiss Ephemeris ─────────────────────────────────────
print("  Swiss Ephemeris")
print("  " + "─" * 45)

def check_swisseph():
    import swisseph as swe
    return True, f"v{swe.version}"
check("Swiss Ephemeris", check_swisseph)

# ─── Astro Engine ────────────────────────────────────────
print()
print("  Astro Engine")
print("  " + "─" * 45)

def check_planets():
    c = calculate_chart(**CHART_ROBERTO)
    return len(c["planetas"]) == 10, f"{len(c['planetas'])} planetas"
check("Planetas (10)", check_planets)

def check_houses():
    c = calculate_chart(**CHART_ROBERTO)
    return len(c["casas"]) == 12, f"{len(c['casas'])} casas"
check("Casas (12)", check_houses)

def check_asc():
    c = calculate_chart(**CHART_ROBERTO)
    return c["ascendente"]["signo"] == "Touro", c["ascendente"]["formatado"]
check("Ascendente", check_asc)

def check_mc():
    c = calculate_chart(**CHART_ROBERTO)
    return c["meio_do_ceu"]["signo"] == "Peixes", c["meio_do_ceu"]["formatado"]
check("Meio do Céu", check_mc)

def check_deltat():
    c = calculate_chart(**CHART_ROBERTO)
    dt = c["meta"]["delta_t_segundos"]
    return dt > 0, f"DeltaT={dt}s"
check("DeltaT", check_deltat)

def check_speed():
    c = calculate_chart(**CHART_ROBERTO)
    speed = c["planetas"]["Sol"].get("speed_longitude")
    return speed is not None and speed > 0, f"Sol speed={speed}"
check("Planet Speed", check_speed)

def check_retro():
    c = calculate_chart(**CHART_ROBERTO)
    mer = c["planetas"]["Mercúrio"]
    retro_flag = mer.get("retrogrado") is True
    speed_neg = mer.get("speed_longitude", 0) < 0
    return retro_flag and speed_neg, f"speed={mer.get('speed_longitude')}"
check("Retrogrades", check_retro)

# ─── Aspect Engine ───────────────────────────────────────
print()
print("  Aspect Engine")
print("  " + "─" * 45)

def check_aspects():
    c = calculate_chart(**CHART_ROBERTO)
    objs = objects_from_chart(c)
    aspects = detect_aspects(objs)
    return len(aspects) > 0, f"{len(aspects)} aspectos"
check("Aspect Engine", check_aspects)

def check_phase():
    c = calculate_chart(**CHART_ROBERTO)
    objs = objects_from_chart(c)
    aspects = detect_aspects(objs)
    phases = set(a["phase"] for a in aspects)
    valid = phases.issubset({"applying","separating","exact"})
    return valid, f"phases={phases}"
check("Phase values", check_phase)

def check_ids():
    c = calculate_chart(**CHART_ROBERTO)
    objs = objects_from_chart(c)
    aspects = detect_aspects(objs)
    ids = [a["id"] for a in aspects]
    return len(ids) == len(set(ids)), f"{len(aspects)} únicos"
check("IDs únicos", check_ids)

# ─── Query Engine ────────────────────────────────────────
print()
print("  Query Engine")
print("  " + "─" * 45)

from query.query_engine import QueryEngine, QueryNotFoundError

def check_query_engine():
    c = calculate_chart(**CHART_ROBERTO)
    objs = objects_from_chart(c)
    aspects = detect_aspects(objs)
    qe = QueryEngine(c, aspects)
    result = qe.execute("resumo_mapa")
    return result["total_aspectos"] == 19, f"{result['total_aspectos']} aspectos"
check("Query Engine", check_query_engine)

def check_query_not_found():
    c = calculate_chart(**CHART_ROBERTO)
    qe = QueryEngine(c, [])
    try:
        qe.execute("query_inexistente")
        return False, "deveria ter levantado QueryNotFoundError"
    except QueryNotFoundError:
        return True, "QueryNotFoundError OK"
check("QueryNotFoundError", check_query_not_found)

def check_stellium():
    c = calculate_chart(**CHART_ROBERTO)
    objs = objects_from_chart(c)
    aspects = detect_aspects(objs)
    qe = QueryEngine(c, aspects)
    resumo = qe.execute("resumo_mapa")
    return "Virgem" in resumo["stellium"], f"stellium={resumo['stellium']}"
check("Stellium detection", check_stellium)

# ─── Aspect Explorer ─────────────────────────────────────
print()
print("  Aspect Explorer")
print("  " + "─" * 45)

def check_explorer_json():
    import subprocess
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        fname = f.name
    result = subprocess.run([
        sys.executable, "explorer/aspect_explorer.py",
        "--date", "1957-08-29", "--time", "00:00",
        "--lat", "-22.9833", "--lon", "-49.8667", "--tz", "-3",
        "--name", "Teste", "--json", fname
    ], capture_output=True, text=True,
       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if result.returncode != 0:
        return False, result.stderr[:80]
    with open(fname) as f:
        data = json.load(f)
    os.unlink(fname)
    return len(data) > 0, f"{len(data)} aspectos exportados"
check("JSON Export", check_explorer_json)

def check_explorer_csv():
    import subprocess
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        fname = f.name
    result = subprocess.run([
        sys.executable, "explorer/aspect_explorer.py",
        "--date", "1957-08-29", "--time", "00:00",
        "--lat", "-22.9833", "--lon", "-49.8667", "--tz", "-3",
        "--name", "Teste", "--csv", fname
    ], capture_output=True, text=True,
       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if result.returncode != 0:
        return False, result.stderr[:80]
    with open(fname) as f:
        lines = f.readlines()
    os.unlink(fname)
    return len(lines) > 1, f"{len(lines)-1} linhas"
check("CSV Export", check_explorer_csv)

# ─── Timeline Engine ─────────────────────────────────────
print()
print("  Timeline Engine")
print("  " + "─" * 45)

from timeline.timeline_engine import generate as timeline_generate

def check_timeline_basic():
    from datetime import datetime
    events = list(timeline_generate(
        datetime(2026, 7, 1), datetime(2026, 7, 3), step="1d"
    ))
    return len(events) == 3, f"{len(events)} instantes gerados"
check("Timeline generate", check_timeline_basic)

def check_timeline_moon():
    from datetime import datetime
    events = list(timeline_generate(
        datetime(2026, 7, 1), datetime(2026, 7, 1), step="1d"
    ))
    return "MOON" in events[0]["planets"], f"Lua={events[0]['planets']['MOON']['signo']}"
check("Lua presente", check_timeline_moon)

def check_timeline_filter():
    from datetime import datetime
    events = list(timeline_generate(
        datetime(2026, 7, 1), datetime(2026, 7, 3), step="1d",
        filters={"objects": ["MOON", "VEN"]}
    ))
    for e in events:
        for asp in e["aspects"]:
            if asp["object1_id"] not in ["MOON","VEN"] and asp["object2_id"] not in ["MOON","VEN"]:
                return False, "aspecto fora do filtro encontrado"
    return True, "filtro OK"
check("Filtro objects", check_timeline_filter)

# ─── Knowledge Engine ────────────────────────────────────
print()
print("  Knowledge Engine")
print("  " + "─" * 45)

from knowledge_engine.knowledge_engine import load_package, execute, KnowledgeValidationError, KnowledgePackageNotFound, _validate_rule

def check_load_package():
    pkg = load_package('astrohair')
    return len(pkg['rules']) == 5, f"{len(pkg['rules'])} regras ativas"
check("Load package AstroHair", check_load_package)

def check_schema_validation():
    try:
        _validate_rule({'id': 'TEST', 'product': 'test'}, 'test.yaml')
        return False, "deveria ter lançado exceção"
    except KnowledgeValidationError:
        return True, "KnowledgeValidationError OK"
check("Schema validation", check_schema_validation)

def check_package_not_found():
    try:
        load_package('astromarket')
        return False, "deveria ter lançado exceção"
    except KnowledgePackageNotFound:
        return True, "KnowledgePackageNotFound OK"
check("Package not found", check_package_not_found)

def check_execute():
    from datetime import datetime
    from timeline.timeline_engine import generate
    pkg = load_package('astrohair')
    events = list(generate(datetime(2026,7,1), datetime(2026,7,1), step='1d'))
    result = execute(events[0], pkg)
    has_rules = len(result['triggered_rules']) > 0
    has_score = len(result['total_score']) > 0
    return has_rules and has_score, f"{len(result['triggered_rules'])} regras disparadas"
check("Execute rules", check_execute)

# ─── Resultado Final ─────────────────────────────────────
total = len(results)
passed = sum(results)
failed = total - passed

print()
print("  " + "═" * 45)
if failed == 0:
    print(f"  \033[92m✓ Todos os {total} checks passaram. Sistema saudável.\033[0m")
else:
    print(f"  \033[91m✗ {failed}/{total} checks falharam.\033[0m")
print("  " + "═" * 45)
print()

sys.exit(0 if failed == 0 else 1)
