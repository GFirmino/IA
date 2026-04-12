from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional


PLATE_PATTERNS = [
    re.compile(r"([A-Z]{2}-\d{2}-[A-Z]{2})"),
    re.compile(r"(\d{2}-[A-Z]{2}-\d{2})"),
    re.compile(r"(\d{2}-\d{2}-[A-Z]{2})"),
    re.compile(r"([A-Z]{2}-\d{2}-\d{2})"),
]


def normalize_plate(text: str) -> Optional[str]:
    if not text:
        return None

    cleaned = text.upper().strip()

    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace("_", "-")
    cleaned = cleaned.replace(".", "-")
    cleaned = cleaned.replace(":", "-")
    cleaned = cleaned.replace("—", "-")
    cleaned = cleaned.replace("–", "-")
    cleaned = cleaned.replace("|", "")
    cleaned = cleaned.replace("/", "")
    cleaned = cleaned.replace("\\", "")

    simple_for_check = re.sub(r"[^A-Z0-9]", "", cleaned)
    if re.fullmatch(r"[O0]{2}[A-Z]{2}[O0]{2}", simple_for_check):
        cleaned = cleaned.replace("O", "0")

    candidates = {cleaned}

    simple = re.sub(r"[^A-Z0-9]", "", cleaned)
    if len(simple) == 6:
        candidates.add(f"{simple[:2]}-{simple[2:4]}-{simple[4:]}")

    for candidate in candidates:
        for rx in PLATE_PATTERNS:
            match = rx.search(candidate)
            if match:
                return match.group(1)

    return None


def _try_easyocr(path: Path) -> Optional[str]:
    try:
        import easyocr
        from PIL import Image, ImageOps, ImageFilter

        reader = easyocr.Reader(["en"], gpu=False)

        variants = []
        original = Image.open(path)

        variants.append(original)

        gray = ImageOps.grayscale(original)
        gray = ImageOps.autocontrast(gray)
        variants.append(gray)

        sharp = gray.filter(ImageFilter.SHARPEN)
        variants.append(sharp)

        bw = gray.point(lambda x: 0 if x < 160 else 255, "1").convert("L")
        variants.append(bw)

        for img in variants:
            results = reader.readtext(img, detail=0)
            print("EASYOCR RAW:", results)

            for text in results:
                plate = normalize_plate(text)
                if plate:
                    return plate

    except Exception as e:
        print("Erro EasyOCR:", e)

    return None


def _configure_tesseract(pytesseract_module) -> None:
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for exe_path in possible_paths:
        if os.path.exists(exe_path):
            pytesseract_module.pytesseract.tesseract_cmd = exe_path
            print("Tesseract encontrado em:", exe_path)
            return

    # Se não encontrar, deixa como está; pode estar no PATH
    print("Tesseract não encontrado nos caminhos padrão. A tentar via PATH...")


def _try_tesseract(path: Path) -> Optional[str]:
    try:
        import pytesseract
        from PIL import Image, ImageOps, ImageFilter

        _configure_tesseract(pytesseract)

        original = Image.open(path)

        variants = []

        gray = ImageOps.grayscale(original)
        gray = ImageOps.autocontrast(gray)
        variants.append(gray)

        sharp = gray.filter(ImageFilter.SHARPEN)
        variants.append(sharp)

        bw1 = gray.point(lambda x: 0 if x < 140 else 255, "1").convert("L")
        variants.append(bw1)

        bw2 = gray.point(lambda x: 0 if x < 170 else 255, "1").convert("L")
        variants.append(bw2)

        bw3 = gray.point(lambda x: 0 if x < 190 else 255, "1").convert("L")
        variants.append(bw3)

        configs = [
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
            '--psm 13 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
        ]

        for img in variants:
            for config in configs:
                text = pytesseract.image_to_string(img, config=config)
                print("TESSERACT RAW:", repr(text))

                plate = normalize_plate(text)
                if plate:
                    return plate

    except Exception as e:
        print("Erro Tesseract:", e)

    return None


def extract_plate_from_image(image_path: str) -> Optional[str]:
    path = Path(image_path)
    if not path.exists():
        print("Imagem não encontrada:", path)
        return None

    print("A processar imagem:", path)

    plate = _try_easyocr(path)
    if plate:
        print("Matrícula encontrada com EasyOCR:", plate)
        return plate

    plate = _try_tesseract(path)
    if plate:
        print("Matrícula encontrada com Tesseract:", plate)
        return plate

    plate = normalize_plate(path.stem)
    if plate:
        print("Matrícula encontrada pelo nome do ficheiro:", plate)
        return plate

    print("Não foi possível extrair matrícula.")
    return None