"""
Kalon Astro Engine — Knowledge Calibrator
Sistema de Calibração de Conhecimento Astrológico.

Fluxo:
  1. Você abre o SolarFire e gera a interpretação de um evento específico
  2. Cola o texto aqui (ou passa como argumento)
  3. A IA extrai APENAS os temas — o texto original é descartado
  4. O resultado é gravado em YAML no banco de conhecimento Kalon

Filosofia:
  - O SolarFire é um professor, não uma fonte
  - Nenhum texto protegido é armazenado
  - Apenas conceitos e temas são preservados
  - Roberto revisa e aprova cada entrada

Copyright: O texto do SolarFire é usado apenas como insumo temporário.
Nenhum trecho é reproduzido ou armazenado no sistema Kalon.
"""

import anthropic
import yaml
import json
import os
import sys
import argparse
from datetime import datetime

# ─── Paths ───────────────────────────────────────────────

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KB_PATH = os.path.join(_BASE, "knowledge_base", "calibrated.yaml")
os.makedirs(os.path.dirname(_KB_PATH), exist_ok=True)

# ─── Prompt de extração ──────────────────────────────────

EXTRACTION_PROMPT = """Você é um assistente de catalogação de conhecimento astrológico.

Receberá o texto de uma interpretação astrológica do SolarFire para o evento: {event_id}

Sua tarefa é extrair APENAS os conceitos e temas — NÃO reproduza nenhuma frase do texto original.

Retorne APENAS um JSON válido com esta estrutura:
{{
  "event_id": "{event_id}",
  "themes": ["lista", "de", "temas", "em", "portugues"],
  "polarity": "positive" | "negative" | "neutral" | "mixed",
  "intensity": "low" | "medium" | "high",
  "domains": ["hair", "love", "cash", "diet", "wellbeing", "career", "family", "spiritual"],
  "keywords": ["palavras", "chave", "em", "portugues"],
  "contraindications": ["o que evitar durante este aspecto"],
  "favorable_for": ["o que é favorecido durante este aspecto"],
  "psychological": "uma frase neutra sobre o estado psicológico (SUA PRÓPRIA FRASE, não copiada)",
  "confidence": 0.85
}}

IMPORTANTE:
- themes: máximo 8 temas concisos em português
- domains: apenas os domínios Kalon relevantes (pode ser vazio se não aplicável)
- psychological: escreva com suas próprias palavras, não copie
- confidence: sua confiança na extração (0.0 a 1.0)
- NÃO inclua nenhum texto do SolarFire na resposta

Texto do SolarFire para análise:
---
{solarfire_text}
---

Responda APENAS com o JSON. Sem explicações adicionais."""


# ─── Funções principais ──────────────────────────────────

def extract_themes(event_id: str, solarfire_text: str) -> dict:
    """
    Usa IA para extrair temas de uma interpretação do SolarFire.
    O texto original é descartado — apenas os conceitos são preservados.
    """
    client = anthropic.Anthropic()
    
    prompt = EXTRACTION_PROMPT.format(
        event_id=event_id,
        solarfire_text=solarfire_text
    )
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = response.content[0].text.strip()
    
    # Limpar possíveis markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    result = json.loads(raw)
    result["calibrated_at"] = datetime.now().isoformat()
    result["source"] = "solarfire_calibration"
    result["reviewed"] = False  # Roberto precisa revisar
    
    return result


def load_knowledge_base() -> dict:
    """Carrega a base de conhecimento calibrada."""
    if os.path.exists(_KB_PATH):
        with open(_KB_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {"entries": {}}
    return {"entries": {}}


def save_to_knowledge_base(entry: dict) -> None:
    """Salva uma entrada calibrada na base de conhecimento."""
    kb = load_knowledge_base()
    
    event_id = entry["event_id"]
    kb["entries"][event_id] = entry
    kb["last_updated"] = datetime.now().isoformat()
    kb["total_entries"] = len(kb["entries"])
    
    with open(_KB_PATH, "w", encoding="utf-8") as f:
        yaml.dump(kb, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"\n✅ Entrada '{event_id}' salva em knowledge_base/calibrated.yaml")


def review_entry(entry: dict) -> dict:
    """Interface de revisão para Roberto aprovar ou ajustar a entrada."""
    print("\n" + "="*60)
    print("REVISÃO — Knowledge Calibrator")
    print("="*60)
    print(f"\nEvento: {entry['event_id']}")
    print(f"Polaridade: {entry['polarity']}")
    print(f"Intensidade: {entry['intensity']}")
    print(f"Confiança IA: {entry['confidence']}")
    print(f"\nTemas: {', '.join(entry.get('themes', []))}")
    print(f"Domínios: {', '.join(entry.get('domains', []))}")
    print(f"Palavras-chave: {', '.join(entry.get('keywords', []))}")
    print(f"\nFavorável para: {', '.join(entry.get('favorable_for', []))}")
    print(f"Contraindicações: {', '.join(entry.get('contraindications', []))}")
    print(f"\nPsicológico: {entry.get('psychological', '')}")
    
    print("\n" + "-"*60)
    print("Opções: [A]provar  [E]ditar temas  [R]ejeitar  [S]air")
    choice = input("Sua escolha: ").strip().upper()
    
    if choice == "A":
        entry["reviewed"] = True
        entry["reviewed_at"] = datetime.now().isoformat()
        print("✅ Aprovado!")
        
    elif choice == "E":
        print(f"\nTemas atuais: {entry.get('themes', [])}")
        new_themes = input("Novos temas (separados por vírgula): ").strip()
        if new_themes:
            entry["themes"] = [t.strip() for t in new_themes.split(",")]
        
        print(f"\nDomínios atuais: {entry.get('domains', [])}")
        new_domains = input("Novos domínios (separados por vírgula, ou Enter para manter): ").strip()
        if new_domains:
            entry["domains"] = [d.strip() for d in new_domains.split(",")]
        
        entry["reviewed"] = True
        entry["reviewed_at"] = datetime.now().isoformat()
        print("✅ Editado e aprovado!")
        
    elif choice == "R":
        print("❌ Rejeitado — não será salvo.")
        return None
        
    elif choice == "S":
        print("⏸ Saindo sem salvar.")
        return None
    
    return entry


def list_entries():
    """Lista todas as entradas calibradas."""
    kb = load_knowledge_base()
    entries = kb.get("entries", {})
    
    if not entries:
        print("Nenhuma entrada calibrada ainda.")
        return
    
    print(f"\n{'='*60}")
    print(f"Knowledge Base Calibrada — {len(entries)} entradas")
    print(f"{'='*60}")
    
    for event_id, entry in sorted(entries.items()):
        reviewed = "✅" if entry.get("reviewed") else "⏳"
        polarity = entry.get("polarity", "?")
        themes = ", ".join(entry.get("themes", [])[:3])
        print(f"  {reviewed} {event_id:30s} [{polarity:8s}] {themes}")


def generate_event_list():
    """Gera a lista de eventos astrológicos para calibrar."""
    planets = ["Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    aspects = ["CON", "OPP", "TRI", "SQR", "SEX"]
    
    events = []
    for i, p1 in enumerate(planets):
        for p2 in planets[i+1:]:
            for asp in aspects:
                events.append(f"{p1[:3].upper()}_{asp}_{p2[:3].upper()}")
    
    # Planetas em casas (Moon in House 1-12)
    for p in ["Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
        for h in range(1, 13):
            events.append(f"{p[:3].upper()}_H{h:02d}")
    
    print(f"\nTotal de eventos para calibrar: {len(events)}")
    print("Primeiros 20:")
    for e in events[:20]:
        print(f"  {e}")
    
    return events


# ─── CLI ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Kalon Knowledge Calibrator — extrai temas de interpretações astrológicas"
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Comando: calibrate
    cal = subparsers.add_parser("calibrate", help="Calibrar um evento")
    cal.add_argument("event_id", help="ID do evento (ex: MOO_TRI_VEN)")
    cal.add_argument("--text", "-t", help="Texto do SolarFire (ou omitir para digitar)")
    cal.add_argument("--file", "-f", help="Arquivo .txt com a interpretação do SolarFire")
    cal.add_argument("--no-review", action="store_true", help="Salvar sem revisão manual")
    
    # Comando: list
    subparsers.add_parser("list", help="Listar entradas calibradas")
    
    # Comando: events
    subparsers.add_parser("events", help="Listar eventos para calibrar")
    
    args = parser.parse_args()
    
    if args.command == "calibrate":
        # Obter texto do SolarFire
        if args.file:
            with open(args.file, encoding="utf-8") as f:
                solarfire_text = f.read()
        elif args.text:
            solarfire_text = args.text
        else:
            print(f"Cole a interpretação do SolarFire para '{args.event_id}'")
            print("(Pressione Ctrl+D quando terminar)")
            lines = []
            try:
                while True:
                    lines.append(input())
            except EOFError:
                pass
            solarfire_text = "\n".join(lines)
        
        if not solarfire_text.strip():
            print("Erro: nenhum texto fornecido.")
            sys.exit(1)
        
        print(f"\n🔍 Extraindo temas para '{args.event_id}'...")
        entry = extract_themes(args.event_id, solarfire_text)
        
        if args.no_review:
            save_to_knowledge_base(entry)
        else:
            reviewed = review_entry(entry)
            if reviewed:
                save_to_knowledge_base(reviewed)
    
    elif args.command == "list":
        list_entries()
    
    elif args.command == "events":
        generate_event_list()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
