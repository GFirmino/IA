from __future__ import annotations

from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = ROOT / "history"
JSON_PATH = HISTORY_DIR / "search_history.json"
CSV_PATH = HISTORY_DIR / "search_history.csv"


def read_history() -> list[dict]:
    HISTORY_DIR.mkdir(exist_ok=True)

    if not JSON_PATH.exists():
        return []

    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def save_history_entry(entry: dict):
    HISTORY_DIR.mkdir(exist_ok=True)

    history = read_history()
    history.append(entry)

    JSON_PATH.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    row = {
        "timestamp": entry["timestamp"],
        "plate": entry["vehicle"].get("detected_plate"),
        "owner": entry["vehicle"].get("owner", "N/D"),
        "vehicle": entry["vehicle"].get("vehicle", "N/D"),
        "origin": entry["origin"],
        "goal": entry["goal"],
        "algorithm": entry["algorithm"],
        "depth_limit": entry.get("depth_limit"),
        "summary": summarize_results(entry["results"]),
    }

    write_header = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def summarize_results(results: dict) -> str:
    chunks = []

    pretty_names = {
        "ucs": "Custo Uniforme",
        "dls": "Profundidade Limitada",
        "greedy": "Procura Sôfrega",
        "astar": "A*",
    }

    for name, result in results.items():
        algorithm_name = pretty_names.get(name, name)
        path = " → ".join(result["path"]) if result["path"] else "sem caminho"
        cost = result.get("cost", "N/D")
        chunks.append(f"{algorithm_name}: {path} ({cost} km)")

    return " | ".join(chunks)


def build_history_table(history: list[dict]) -> list[dict]:
    pretty_names = {
        "all": "Todos",
        "ucs": "Custo Uniforme",
        "dls": "Profundidade Limitada",
        "greedy": "Procura Sôfrega",
        "astar": "A*",
    }

    rows = []

    for entry in reversed(history):  # mais recente primeiro
        vehicle_info = entry.get("vehicle", {})
        results = entry.get("results", {})

        rows.append({
            "Data/Hora": entry.get("timestamp", ""),
            "Matrícula": vehicle_info.get("detected_plate", "N/D"),
            "Proprietário": vehicle_info.get("owner", "N/D"),
            "Veículo": vehicle_info.get("vehicle", "N/D"),
            "Origem": entry.get("origin", ""),
            "Destino": entry.get("goal", ""),
            "Algoritmo": pretty_names.get(entry.get("algorithm", ""), entry.get("algorithm", "")),
            "Resumo": summarize_results(results),
        })

    return rows