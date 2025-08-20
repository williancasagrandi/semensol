# app/utils/face_utils.py
import os
import cv2
import math
import logging
import numpy as np
import face_recognition
from typing import Tuple, Optional, List, Any

from app.models import Motorista

# ------------------ Config ------------------
FACE_DETECTOR_MODEL = os.getenv("FACE_DETECTOR_MODEL", "hog")   # "cnn" se dlib-cnn
FACE_UPSAMPLE = int(os.getenv("FACE_UPSAMPLE", "1"))            # upsample para faces pequenas
NUM_JITTERS = int(os.getenv("FACE_NUM_JITTERS", "3"))
DEFAULT_TOL = float(os.getenv("FACE_TOLERANCIA", "0.6"))

MIN_FOCUS_VAR = float(os.getenv("FACE_MIN_FOCUS_VAR", "60.0"))
MIN_BRIGHTNESS = float(os.getenv("FACE_MIN_BRIGHTNESS", "40.0"))
MAX_BRIGHTNESS = float(os.getenv("FACE_MAX_BRIGHTNESS", "200.0"))
MIN_FACE_SIZE_PX = int(os.getenv("FACE_MIN_SIZE_PX", "80"))

CONF_STEEPNESS_K = float(os.getenv("FACE_CONF_STEEPNESS", "20.0"))

logger = logging.getLogger(__name__)

# ------------------ Utils internos ------------------
def _laplacian_var(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

def _image_to_rgb(image_path: str) -> np.ndarray:
    bgr = cv2.imread(image_path)
    if bgr is None:
        raise ValueError(f"Não foi possível ler a imagem em: {image_path}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    return rgb

def _align_by_eyes(rgb_img: np.ndarray, landmarks: dict) -> np.ndarray:
    left_eye = landmarks.get("left_eye")
    right_eye = landmarks.get("right_eye")
    if not left_eye or not right_eye:
        return rgb_img
    left_center = np.mean(left_eye, axis=0)
    right_center = np.mean(right_eye, axis=0)
    dy = float(right_center[1] - left_center[1])
    dx = float(right_center[0] - left_center[0])
    angle = math.degrees(math.atan2(dy, dx))
    h, w = rgb_img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    aligned = cv2.warpAffine(rgb_img, M, (w, h), flags=cv2.INTER_LINEAR)
    return aligned

def _detect_faces(rgb_img: np.ndarray) -> List[Tuple[int, int, int, int]]:
    return face_recognition.face_locations(
        rgb_img,
        number_of_times_to_upsample=FACE_UPSAMPLE,
        model=FACE_DETECTOR_MODEL
    )

def _ensure_rgb_uint8_c_contig(img: np.ndarray) -> np.ndarray:
    # garante 3 canais RGB, uint8 e memória contígua (requisito do dlib)
    out = img
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2RGB)
    elif out.shape[2] == 4:
        out = cv2.cvtColor(out, cv2.COLOR_RGBA2RGB)
    if out.dtype != np.uint8:
        out = out.astype(np.uint8)
    if not out.flags.c_contiguous:
        out = np.ascontiguousarray(out)
    return out

def _extract_single_face(rgb_img: np.ndarray) -> Optional[np.ndarray]:
    """
    Detecta UMA face. Alinha por olhos e recorta. Se !=1 face, retorna None.
    Retorna recorte normalizado (RGB, uint8, C-contiguous).
    """
    boxes = _detect_faces(rgb_img)
    if len(boxes) != 1:
        return None

    top, right, bottom, left = boxes[0]
    face = rgb_img[top:bottom, left:right]

    # Alinhamento e redetecção
    lmarks = face_recognition.face_landmarks(rgb_img, [boxes[0]])
    if lmarks:
        aligned = _align_by_eyes(rgb_img, lmarks[0])
        boxes_aligned = _detect_faces(aligned)
        if len(boxes_aligned) >= 1:
            t, r, b, l = boxes_aligned[0]
            face = aligned[t:b, l:r]

    return _ensure_rgb_uint8_c_contig(face)

def _quality_checks(face_img: np.ndarray) -> Tuple[bool, dict]:
    h, w = face_img.shape[:2]
    if min(h, w) < MIN_FACE_SIZE_PX:
        return False, {"focus": 0.0, "brightness": 0.0, "h": h, "w": w, "reason": "Tamanho insuficiente"}

    gray = cv2.cvtColor(face_img, cv2.COLOR_RGB2GRAY)
    focus = _laplacian_var(gray)
    brightness = float(np.mean(gray))

    ok = (focus >= MIN_FOCUS_VAR) and (MIN_BRIGHTNESS <= brightness <= MAX_BRIGHTNESS)
    metrics = {"focus": focus, "brightness": brightness, "h": h, "w": w}
    if not ok:
        reason = "Foco baixo" if focus < MIN_FOCUS_VAR else "Brilho inadequado"
        return False, {**metrics, "reason": reason}
    return True, {**metrics, "reason": "ok"}

def _encode_face(face_img: np.ndarray) -> Optional[np.ndarray]:
    """
    Extrai encoding 128-D do recorte de face normalizado.
    Usa known_face_locations para evitar nova detecção.
    """
    face_img = _ensure_rgb_uint8_c_contig(face_img)
    h, w = face_img.shape[:2]
    enc = face_recognition.face_encodings(
        face_img,
        known_face_locations=[(0, w, h, 0)],
        num_jitters=NUM_JITTERS,
        model="small"
    )
    return enc[0] if enc else None

def _dist_to_conf(distance: float, tol: float) -> float:
    x = distance - tol
    conf = 1.0 / (1.0 + math.exp(CONF_STEEPNESS_K * x))
    return float(max(0.0, min(1.0, conf)))

def _to_numpy_encoding(raw: Any) -> Optional[np.ndarray]:
    """
    Converte bytes/list/ndarray para np.ndarray (128,) float64.
    Aceita buffers 512 bytes (float32) e 1024 bytes (float64).
    """
    if raw is None:
        return None
    if isinstance(raw, np.ndarray):
        arr = raw
    elif isinstance(raw, (bytes, bytearray, memoryview)):
        buf = memoryview(raw)
        if len(buf) == 128 * 8:
            arr = np.frombuffer(buf, dtype=np.float64)
        elif len(buf) == 128 * 4:
            arr = np.frombuffer(buf, dtype=np.float32)
        else:
            return None
    elif isinstance(raw, (list, tuple)):
        arr = np.asarray(raw, dtype=np.float64)
    else:
        return None

    arr = np.asarray(arr)
    if arr.ndim != 1:
        arr = arr.reshape(-1)
    if arr.shape[0] != 128:
        return None
    return arr.astype(np.float64, copy=False)

# ------------------ API pública ------------------
def validar_qualidade_imagem(imagem_path: str) -> Tuple[bool, str]:
    try:
        rgb = _image_to_rgb(imagem_path)
        face = _extract_single_face(rgb)
        if face is None:
            return False, "Imagem deve conter exatamente um rosto detectável"
        ok, m = _quality_checks(face)
        if not ok:
            return False, f"Qualidade insuficiente (foco={m['focus']:.1f}, brilho={m['brightness']:.1f}, tamanho={m['w']}x{m['h']})"
        return True, "Imagem válida"
    except Exception as e:
        logger.error("Erro em validar_qualidade_imagem: %s", e, exc_info=True)
        return False, f"Erro ao validar imagem: {e}"

def extrair_biometria_facial(imagem_path: str) -> Optional[np.ndarray]:
    try:
        rgb_img = _image_to_rgb(imagem_path)
        face_img = _extract_single_face(rgb_img)
        if face_img is None:
            return None
        ok, _ = _quality_checks(face_img)
        if not ok:
            return None
        return _encode_face(face_img)
    except Exception as e:
        logger.error("Falha ao extrair biometria (%s): %s", imagem_path, e, exc_info=True)
        return None

def comparar_biometrias(encoding_conhecido: np.ndarray,
                        encoding_desconhecido: np.ndarray,
                        tolerancia: float = DEFAULT_TOL) -> Tuple[bool, float]:
    a = _to_numpy_encoding(encoding_conhecido)
    b = _to_numpy_encoding(encoding_desconhecido)
    if a is None or b is None:
        return False, 0.0
    dist = float(face_recognition.face_distance(np.expand_dims(a, 0), b)[0])
    conf = _dist_to_conf(dist, tolerancia)
    return (dist <= tolerancia), conf

def reconhecer_motorista_por_id(imagem_path: str, motorista_id: int, tolerancia: float = DEFAULT_TOL) -> Tuple[bool, float]:
    m_obj = Motorista.query.get(motorista_id)
    if not m_obj:
        return False, 0.0

    ref = _to_numpy_encoding(m_obj.get_biometria())
    if ref is None:
        return False, 0.0

    enc_img = extrair_biometria_facial(imagem_path)
    if enc_img is None:
        return False, 0.0

    return comparar_biometrias(ref, enc_img, tolerancia)

def encontrar_correspondencia(encoding_alvo: np.ndarray,
                              candidatos: List[Tuple[Any, np.ndarray]],
                              tolerancia: float = DEFAULT_TOL) -> Tuple[Optional[Any], float]:
    if not candidatos:
        return None, 0.0

    objs = [c[0] for c in candidatos]
    vecs = np.stack([_to_numpy_encoding(c[1]) for c in candidatos], axis=0)
    # Remover candidatos inválidos
    mask_valid = np.array([v is not None for v in [*map(_to_numpy_encoding, [c[1] for c in candidatos])]], dtype=bool)
    if not mask_valid.any():
        return None, 0.0
    vecs = np.stack([_to_numpy_encoding(c[1]) for c in candidatos if _to_numpy_encoding(c[1]) is not None], axis=0)
    objs = [c[0] for c in candidatos if _to_numpy_encoding(c[1]) is not None]

    enc_alvo = _to_numpy_encoding(encoding_alvo)
    if enc_alvo is None:
        return None, 0.0

    dists = face_recognition.face_distance(vecs, enc_alvo)
    idx = int(np.argmin(dists))
    best_dist = float(dists[idx])
    conf = _dist_to_conf(best_dist, tolerancia)
    return (objs[idx], conf) if best_dist <= tolerancia else (None, conf)

def reconhecer_motorista_cadastrado(imagem_path: str, tolerancia: float = DEFAULT_TOL) -> Tuple[Optional[Motorista], float]:
    """
    Identificação 1:N. Itera pela base e escolhe o melhor candidato.
    Para grandes volumes, substitua por um índice vetorial (FAISS/Milvus/pgvector).
    """
    enc_img = extrair_biometria_facial(imagem_path)
    if enc_img is None:
        return None, 0.0

    candidatos: List[Tuple[Motorista, np.ndarray]] = []
    for m in Motorista.query.all():
        ref = _to_numpy_encoding(m.get_biometria())
        if ref is not None:
            candidatos.append((m, ref))

    if not candidatos:
        return None, 0.0

    obj, conf = encontrar_correspondencia(enc_img, candidatos, tolerancia)
    return obj, conf
