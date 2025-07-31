import serial
import time
import re
import logging
from app.config import (
    SERIAL_PORT, SERIAL_BAUDRATE, SERIAL_TIMEOUT,
    SERIAL_RETRIES, READ_SLEEP, READ_BYTES
)

logger = logging.getLogger(__name__)

def conectar(porta: str = SERIAL_PORT) -> serial.Serial:
    """
    Estabelece conexão serial com a balança TC420.
    Retorna objeto serial.Serial conectado ou lança exceção após tentativas.
    """
    for attempt in range(1, SERIAL_RETRIES + 1):
        try:
            ser = serial.Serial(
                porta,
                baudrate=SERIAL_BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                timeout=SERIAL_TIMEOUT
            )
            logger.info(f"[TC420] Conectado na porta {porta}")
            return ser
        except serial.SerialException as e:
            logger.warning(f"[{attempt}/{SERIAL_RETRIES}] Falha ao conectar na porta {porta}: {e}")
            time.sleep(1)

    raise serial.SerialException(f"Erro: não foi possível abrir a porta {porta} após {SERIAL_RETRIES} tentativas.")

def ler_peso(ser: serial.Serial) -> float:
    """
    Envia comando ENQ e lê resposta da balança.
    Extrai e retorna peso em kg. Retorna 0.0 em caso de falha.
    """
    try:
        ser.write(b'\x05')  # ENQ
        time.sleep(READ_SLEEP)

        resposta = ser.read(READ_BYTES).decode('ascii', errors='ignore').strip()
        logger.debug(f"[TC420] Resposta crua: {resposta!r}")

        # Exemplo de resposta esperada: p`000030000000
        match = re.search(r"p`(\d{12})", resposta)
        if match:
            peso = int(match.group(1)) / 1_000_000
            logger.info(f"[TC420] Peso lido: {peso} kg")
            return peso

        logger.warning("[TC420] Padrão não encontrado na resposta da balança.")
        return 0.0

    except Exception as e:
        logger.error(f"[TC420] Erro ao ler peso: {e}", exc_info=True)
        return 0.0
