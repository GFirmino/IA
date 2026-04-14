from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List
import math

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

CITY_COORDS = {
    "Aveiro": (-8.6538, 40.6405),
    "Beja": (-7.8632, 38.0151),
    "Braga": (-8.4265, 41.5454),
    "Bragança": (-6.7567, 41.8060),
    "Castelo Branco": (-7.4909, 39.8222),
    "Coimbra": (-8.4292, 40.2033),
    "Évora": (-7.9135, 38.5710),
    "Faro": (-7.9304, 37.0194),
    "Guarda": (-7.2658, 40.5373),
    "Leiria": (-8.8070, 39.7436),
    "Lisboa": (-9.1393, 38.7223),
    "Portalegre": (-7.4312, 39.2967),
    "Porto": (-8.6291, 41.1579),
    "Santarém": (-8.6859, 39.2362),
    "Setúbal": (-8.8882, 38.5244),
    "Viana do Castelo": (-8.8345, 41.6932),
    "Vila Real": (-7.7458, 41.3006),
    "Viseu": (-7.9140, 40.6610),
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

def heuristic(city_a: str, city_b: str) -> float:
    """Calcula a distância em linha reta (Euclidiana) entre duas cidades."""
    if city_a not in CITY_COORDS or city_b not in CITY_COORDS:
        return 0.0
    
    x1, y1 = CITY_COORDS[city_a]
    x2, y2 = CITY_COORDS[city_b]
    
    # Cálculo da distância euclidiana multiplicada por um fator para converter em KM
    # (Aproximadamente 111km por grau)
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2) * 111
    return round(dist, 2)

def neighbors(city: str):
    return sorted(GRAPH[city].items(), key=lambda x: x[0])


def path_cost(path: List[str]) -> int:
    total = 0
    for i in range(len(path) - 1):
        total += GRAPH[path[i]][path[i + 1]]
    return total


FALLBACK_ATTRACTIONS = {
  "Aveiro": [
    {"name": "Canais da Ria", "description": "Passeios de moliceiro pelos canais que atravessam a cidade."},
    {"name": "Salinas de Aveiro", "description": "Zona tradicional de produção de sal, com paisagem característica."},
    {"name": "Museu de Aveiro", "description": "Museu instalado no antigo Convento de Jesus, com grande valor histórico."}
  ],
  "Faro": [
    {"name": "Cidade Velha", "description": "Centro histórico muralhado com ruas antigas e edifícios históricos."},
    {"name": "Ria Formosa", "description": "Parque natural conhecido pelas ilhas e diversidade de aves."},
    {"name": "Arco da Vila", "description": "Entrada principal para a zona histórica da cidade."}
  ],
  "Braga": [
    {"name": "Bom Jesus do Monte", "description": "Santuário famoso pela escadaria monumental."},
    {"name": "Sé de Braga", "description": "Uma das catedrais mais antigas de Portugal."},
    {"name": "Jardim de Santa Bárbara", "description": "Jardim no centro da cidade muito conhecido pela sua beleza."}
  ],
  "Lisboa": [
    {"name": "Torre de Belém", "description": "Monumento histórico junto ao rio Tejo."},
    {"name": "Mosteiro dos Jerónimos", "description": "Exemplo marcante da arquitetura manuelina."},
    {"name": "Castelo de São Jorge", "description": "Castelo com vista panorâmica sobre a cidade."}
  ],
  "Porto": [
    {"name": "Ribeira", "description": "Zona histórica junto ao rio Douro, muito visitada."},
    {"name": "Livraria Lello", "description": "Livraria conhecida pela sua arquitetura interior."},
    {"name": "Ponte Dom Luís I", "description": "Ponte icónica que liga Porto a Vila Nova de Gaia."}
  ],
  "Coimbra": [
    {"name": "Universidade de Coimbra", "description": "Uma das universidades mais antigas da Europa."},
    {"name": "Biblioteca Joanina", "description": "Biblioteca histórica com grande valor cultural."},
    {"name": "Mosteiro de Santa Clara-a-Velha", "description": "Ruínas históricas junto ao rio Mondego."}
  ],
  "Viseu": [
    {"name": "Sé de Viseu", "description": "Catedral situada no centro histórico da cidade."},
    {"name": "Museu Grão Vasco", "description": "Museu com obras importantes da pintura portuguesa."},
    {"name": "Parque do Fontelo", "description": "Grande espaço verde muito utilizado pela população."}
  ],
  "Guarda": [
    {"name": "Sé da Guarda", "description": "Catedral imponente situada no ponto mais alto da cidade."},
    {"name": "Torre de Menagem", "description": "Vestígio das antigas muralhas da cidade."},
    {"name": "Parque Natural da Serra da Estrela", "description": "Zona natural com paisagens montanhosas."}
  ],
  "Évora": [
    {"name": "Templo Romano", "description": "Ruínas bem preservadas do período romano."},
    {"name": "Capela dos Ossos", "description": "Capela conhecida pela decoração com ossos humanos."},
    {"name": "Sé de Évora", "description": "Catedral com vista sobre a cidade."}
  ],
  "Leiria": [
    {"name": "Castelo de Leiria", "description": "Castelo medieval com vista sobre a cidade."},
    {"name": "Praça Rodrigues Lobo", "description": "Praça central com esplanadas e comércio."},
    {"name": "Museu de Leiria", "description": "Espaço dedicado à história e cultura local."}
  ],
  "Setúbal": [
    {"name": "Serra da Arrábida", "description": "Paisagens naturais junto ao mar."},
    {"name": "Praia de Galapinhos", "description": "Praia considerada uma das mais bonitas de Portugal."},
    {"name": "Mercado do Livramento", "description": "Mercado tradicional muito conhecido."}
  ],
  "Bragança": [
    {"name": "Castelo de Bragança", "description": "Castelo bem preservado com vista sobre a cidade."},
    {"name": "Domus Municipalis", "description": "Edifício histórico raro em Portugal."},
    {"name": "Parque Natural de Montesinho", "description": "Área natural com grande biodiversidade."}
  ],
  "Vila Real": [
    {"name": "Palácio de Mateus", "description": "Palácio conhecido pela sua arquitetura e jardins."},
    {"name": "Parque Natural do Alvão", "description": "Zona natural com cascatas e trilhos."},
    {"name": "Centro Histórico", "description": "Zona antiga com comércio e património local."}
  ],
  "Beja": [
    {"name": "Castelo de Beja", "description": "Castelo com uma das torres mais altas de Portugal."},
    {"name": "Museu Rainha Dona Leonor", "description": "Museu instalado num antigo convento."},
    {"name": "Centro Histórico", "description": "Zona com ruas tradicionais e edifícios antigos."}
  ],
  "Castelo Branco": [
    {"name": "Jardim do Paço", "description": "Jardim barroco com estátuas e lagos."},
    {"name": "Museu Cargaleiro", "description": "Museu de arte contemporânea."},
    {"name": "Castelo", "description": "Ruínas com vista sobre a cidade."}
  ],
  "Portalegre": [
    {"name": "Castelo de Portalegre", "description": "Castelo com vista sobre a cidade."},
    {"name": "Museu da Tapeçaria", "description": "Museu dedicado à tapeçaria tradicional."},
    {"name": "Serra de São Mamede", "description": "Zona natural com trilhos e paisagens."}
  ]
}

def get_city_attractions_fallback(city_name: str) -> list:
    """
    Devolve as atrações da base de dados estática caso o LLM falhe.
    Se a cidade não existir na base de dados, devolve uma atração genérica.
    """
    return FALLBACK_ATTRACTIONS.get(
        city_name, 
        [{"name": "Centro Histórico", "description": f"Explorar a beleza da cidade de {city_name}."}]
    )
