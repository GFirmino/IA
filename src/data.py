from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List

GRAPH = {
    'Aveiro': {'Porto': 68, 'Viseu': 95, 'Coimbra': 68, 'Leiria': 115},
    'Braga': {'Viana do Castelo': 48, 'Vila Real': 106, 'Porto': 53},
    'Bragança': {'Vila Real': 137, 'Guarda': 202},
    'Beja': {'Évora': 78, 'Faro': 152, 'Setúbal': 142},
    'Castelo Branco': {'Coimbra': 159, 'Guarda': 106, 'Portalegre': 80, 'Évora': 203},
    'Coimbra': {'Viseu': 96, 'Leiria': 67},
    'Évora': {'Lisboa': 150, 'Santarém': 117, 'Portalegre': 131, 'Setúbal': 103},
    'Faro': {'Setúbal': 249, 'Lisboa': 299},
    'Guarda': {'Vila Real': 157, 'Viseu': 85},
    'Leiria': {'Lisboa': 129, 'Santarém': 70},
    'Lisboa': {'Santarém': 78, 'Setúbal': 50},
    'Porto': {'Viana do Castelo': 71, 'Vila Real': 116, 'Viseu': 133},
    'Vila Real': {'Viseu': 110},
}

HEURISTIC_TO_FARO = {
    'Aveiro': 366, 'Braga': 454, 'Bragança': 487, 'Beja': 99, 'Castelo Branco': 280,
    'Coimbra': 319, 'Évora': 157, 'Faro': 0, 'Guarda': 352, 'Leiria': 278,
    'Lisboa': 195, 'Portalegre': 228, 'Porto': 418, 'Santarém': 231, 'Setúbal': 168,
    'Viana do Castelo': 473, 'Vila Real': 429, 'Viseu': 363,
}


def _make_undirected(graph: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
    result = {city: neighbors.copy() for city, neighbors in graph.items()}
    for city, neigh in graph.items():
        result.setdefault(city, {})
        for other, distance in neigh.items():
            result.setdefault(other, {})
            result[other][city] = distance
    return result


GRAPH = _make_undirected(GRAPH)
CITIES = sorted(GRAPH.keys())

def heuristic(city: str, goal: str) -> int:
    return HEURISTIC_TO_FARO.get(city, 0) if goal == 'Faro' else 0


def neighbors(city: str):
    return sorted(GRAPH[city].items(), key=lambda x: x[0])


def path_cost(path: List[str]) -> int:
    total = 0
    for i in range(len(path) - 1):
        total += GRAPH[path[i]][path[i + 1]]
    return total


def get_city_attractions_fallback(city: str):
    fp = Path(__file__).resolve().parent.parent / 'data' / 'city_attractions_fallback.json'
    data = json.loads(fp.read_text(encoding='utf-8'))
    return data.get(city, [
        {'name': f'Centro histórico de {city}', 'description': f'Zona urbana emblemática de {city}.'},
        {'name': f'Monumento principal de {city}', 'description': f'Ponto turístico marcante da cidade de {city}.'},
        {'name': f'Museu de {city}', 'description': f'Espaço cultural representativo da cidade.'},
    ])
