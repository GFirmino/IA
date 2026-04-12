from __future__ import annotations
from datetime import datetime
import json


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def pretty_trace(result: dict) -> str:
    lines = []
    lines.append(f"Sucesso: {result['success']}")
    lines.append(f"Caminho final: {' -> '.join(result['path']) if result['path'] else 'Sem caminho'}")
    lines.append(f"Distância final: {result['cost']}")
    lines.append(f"Nós expandidos: {result['expanded_nodes']}")
    lines.append('Iterações:')
    for idx, step in enumerate(result['iterations'], start=1):
        lines.append(f"  {idx}. {json.dumps(step, ensure_ascii=False)}")
    return '\n'.join(lines)
