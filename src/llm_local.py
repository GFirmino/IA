from __future__ import annotations
import json
import re
import requests
from src.data import get_city_attractions_fallback


def _extract_json_array(text: str):
    match = re.search(r'(\[.*\])', text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
        if isinstance(data, list):
            return data[:3]
    except Exception:
        return None
    return None


def fetch_city_attractions(city: str, model: str = 'llama3.1:8b'):
    prompt = (
        'Responde apenas em JSON válido. '\
        f'Devolve uma lista com exatamente 3 atrações principais da cidade portuguesa "{city}". '\
        'Formato obrigatório: '
        '[{"name":"...","description":"..."},'
        '{"name":"...","description":"..."},'
        '{"name":"...","description":"..."}]. '
        'Cada descrição deve ser curta e objetiva.'
    )
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': model, 'prompt': prompt, 'stream': False},
            timeout=20,
        )
        response.raise_for_status()
        raw = response.json().get('response', '')
        data = _extract_json_array(raw)
        if data and len(data) == 3:
            return data
    except Exception:
        pass
    return get_city_attractions_fallback(city)
