from __future__ import annotations

import json
from pathlib import Path

from src.ocr import extract_plate_from_image, normalize_plate

VEHICLES_PATH = Path(__file__).resolve().parent.parent / "data" / "vehicles.json"


def authenticate_vehicle(plate: str | None = None, image_path: str | None = None) -> dict:
    database = json.loads(VEHICLES_PATH.read_text(encoding="utf-8"))
    valid_plates = {normalize_plate(item["plate"]): item for item in database["vehicles"]}

    detected_plate = None
    source = None

    if plate:
        detected_plate = normalize_plate(plate)
        source = "manual"
    elif image_path:
        detected_plate = extract_plate_from_image(image_path)
        if detected_plate:
            detected_plate = normalize_plate(detected_plate)
        source = "ocr"

    if not detected_plate:
        return {
            "authenticated": False,
            "message": "Não foi possível obter uma matrícula válida.",
            "detected_plate": None,
            "source": source,
        }

    vehicle = valid_plates.get(detected_plate)
    if not vehicle:
        return {
            "authenticated": False,
            "message": f"Matrícula {detected_plate} não autorizada.",
            "detected_plate": detected_plate,
            "source": source,
        }

    return {
        "authenticated": True,
        "message": "Veículo autenticado com sucesso.",
        "detected_plate": detected_plate,
        "source": source,
        "plate": vehicle.get("plate"),
        "owner": vehicle.get("owner"),
        "vehicle": vehicle.get("vehicle"),
        "vehicle_data": vehicle,
    }