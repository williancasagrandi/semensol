# plate_utils.py
import os
import re
import cv2
import numpy as np
import easyocr
from typing import Optional, Tuple, List, Dict

PADRAO_PLACA_BR = re.compile(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$')

# Singleton do OCR
_OCR = None
def _get_reader():
    global _OCR
    if _OCR is None:
        langs = os.getenv("PLATE_OCR_LANGS", "pt").split(",")
        use_gpu = os.getenv("PLATE_OCR_GPU", "false").lower() == "true"
        _OCR = easyocr.Reader(langs, gpu=use_gpu)
    return _OCR


def _clahe_gray(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)

def _unsharp(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (0, 0), 1.0)
    return cv2.addWeighted(gray, 1.5, blur, -0.5, 0)

def _resize_limit(img: np.ndarray, max_w: int = 1280) -> np.ndarray:
    h, w = img.shape[:2]
    if w <= max_w:
        return img
    scale = max_w / w
    return cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

def preprocessar_imagem(imagem_path: str) -> np.ndarray:
    bgr = cv2.imread(imagem_path)
    if bgr is None:
        raise ValueError("Imagem inválida ou caminho inexistente.")
    bgr = _resize_limit(bgr)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = _clahe_gray(gray)
    gray = cv2.bilateralFilter(gray, 7, 60, 60)
    gray = _unsharp(gray)
    return gray  # ndarray, sem arquivo temporário



AMBIG_MAP_LETTER = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z"}
AMBIG_MAP_DIGIT  = {"O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "Q": "0"}

def _corrigir_ambig_posicional(raw: str) -> str:
    txt = re.sub(r'[^A-Z0-9]', '', raw.upper())
    if len(txt) < 7:
        return txt
    # posição dos caracteres na placa: L L L D L/D D D
    chars = list(txt[:7])
    # 1-3 letras
    for i in range(3):
        if chars[i].isdigit():
            chars[i] = AMBIG_MAP_LETTER.get(chars[i], chars[i])
    # 4 dígito
    if chars[3].isalpha():
        chars[3] = AMBIG_MAP_DIGIT.get(chars[3], chars[3])
    # 5 letra OU dígito (já é compatível, mas tendenciar para letra se Mercosul)
    # 6-7 dígitos
    for i in (5, 6):
        if chars[i].isalpha():
            chars[i] = AMBIG_MAP_DIGIT.get(chars[i], chars[i])
    return "".join(chars)

def _aspect_score(w: float, h: float) -> float:
    if h <= 0:
        return 0.0
    ar = w / h
    # score 1.0 perto de 4.0; cai conforme distancia
    return float(max(0.0, 1.0 - abs(ar - 4.0) / 3.0))  # tolera 1–7

def _candidate_score(text_conf: float, area_frac: float, asp_score: float, regex_ok: bool) -> float:
    base = (text_conf or 0.0)
    score = base * (0.4 + 0.3*asp_score + 0.3*min(1.0, area_frac*5))
    if regex_ok:
        score *= 1.15
    return float(score)


def reconhecer_placa(imagem_path: str, debug: bool = False) -> Optional[str]:
    try:
        gray = preprocessar_imagem(imagem_path)
        reader = _get_reader()
        # permitir apenas A-Z0-9
        results = reader.readtext(gray, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", detail=1, paragraph=False)

        H, W = gray.shape[:2]
        best = {"placa": None, "score": 0.0}

        for bbox, texto, conf in results:
            texto_limpo = re.sub(r'[^A-Z0-9]', '', texto.upper())
            # bbox: 4 pontos (x,y)
            x0, y0 = bbox[0]
            x2, y2 = bbox[2]
            w = abs(x2 - x0)
            h = abs(y2 - y0)
            area = w * h
            area_frac = float(area) / float(W * H)
            asp = _aspect_score(w, h)

            txt_corr = _corrigir_ambig_posicional(texto_limpo)
            regex_ok = bool(PADRAO_PLACA_BR.fullmatch(txt_corr))
            score = _candidate_score(conf, area_frac, asp, regex_ok)

            if debug:
                print(f"[conf={conf:.2f}] {texto} -> {txt_corr} | asp={asp:.2f} | area%={area_frac*100:.2f} | score={score:.3f}")

            if score > best["score"]:
                best = {"placa": txt_corr, "score": score}

        return best["placa"]
    except Exception as e:
        if debug:
            print("Erro ao reconhecer placa:", e)
        return None


def reconhecer_placa_multiframe(imagens_paths: List[str]) -> Optional[str]:
    """Agrega múltiplas leituras por voto majoritário simples."""
    votos: Dict[str, int] = {}
    for p in imagens_paths:
        placa = reconhecer_placa(p, debug=False)
        if not placa:
            continue
        votos[placa] = votos.get(placa, 0) + 1
    if not votos:
        return None
    return max(votos.items(), key=lambda kv: kv[1])[0]
