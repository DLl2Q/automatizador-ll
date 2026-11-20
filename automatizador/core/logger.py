"""Logger de la aplicacion: escribe unicamente en la terminal (consola).

La terminal que se abre al iniciar Automatizador (por ejemplo via
ejecutar.bat) se usa como consola de diagnostico en vivo: aqui se registran
los eventos importantes (grabacion, reproduccion, macros guardadas/cargadas,
errores, etc.). A proposito NO se escribe ningun archivo de log en disco:
solo existe mientras la terminal esta abierta, no se almacena nada.
"""

import logging
import sys

_LOGGER_NAME = "automatizador"


def get_logger():
    """Devuelve el logger de la aplicacion, configurado una sola vez para
    imprimir en stdout (la terminal) y nunca en un archivo."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
