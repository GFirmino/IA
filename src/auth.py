import json
from pathlib import Path
from .ocr import extract_plate_from_image # Importa a função que me mostraste

DB_PATH = Path("data/vehicles_db.json")

def load_db():
    if not DB_PATH.exists():
        # Base de dados inicial se o ficheiro não existir
        initial_data = {
            "AA-11-BB": {"owner": "João Silva", "vehicle": "Tesla Model 3"},
            "CC-22-DD": {"owner": "Maria Oliveira", "vehicle": "Renault Zoe"}
        }
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        save_db(initial_data)
        return initial_data
    
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def register_new_vehicle(plate, owner, vehicle_model):
    """Adiciona um novo veículo à base de dados JSON"""
    db = load_db()
    db[plate] = {
        "owner": owner,
        "vehicle": vehicle_model
    }
    save_db(db)

def authenticate_vehicle(plate=None, image_path=None):
    """
    Tenta autenticar por texto direto ou por imagem (OCR).
    """
    db = load_db()
    detected_plate = None
    source = "Manual"

    # 1. Se houver imagem, tenta o OCR primeiro
    if image_path:
        detected_plate = extract_plate_from_image(image_path)
        source = "OCR (Imagem)"
    
    # 2. Se não detetou na imagem mas o utilizador escreveu à mão
    if not detected_plate and plate:
        detected_plate = plate.upper().strip()
        source = "Manual"

    # 3. Verificação na Base de Dados
    if detected_plate in db:
        return {
            "authenticated": True,
            "detected_plate": detected_plate,
            "owner": db[detected_plate]["owner"],
            "vehicle": db[detected_plate]["vehicle"],
            "source": source
        }
    
    # 4. Caso não encontre (para disparar o formulário de registo)
    return {
        "authenticated": False,
        "detected_plate": detected_plate,
        "message": f"Matrícula {detected_plate} não encontrada." if detected_plate else "Nenhuma matrícula detetada."
    }
