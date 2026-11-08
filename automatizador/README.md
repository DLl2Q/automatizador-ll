# Automatizador

Clon basico, hecho en Python, de la idea de **Macro Recorder** (Martels Media):
graba lo que haces con el mouse y el teclado y lo vuelve a reproducir
exactamente igual, respetando los tiempos originales.

## Que incluye

- Grabacion de movimientos de mouse, clics (izq/der/medio), rueda del mouse
  y pulsaciones de teclado, con marca de tiempo relativa.
- Reproduccion fiel a los tiempos grabados, con control de:
  - **Velocidad** (0.1x a 10x).
  - **Repeticiones** (un numero fijo, o 0 = bucle infinito).
- Guardar y cargar macros como archivos `.json` dentro de `macros/`.
- Lista de macros guardadas, con opcion de eliminarlas.
- Casilla para activar/desactivar la grabacion de movimientos del mouse
  (si solo te interesan los clics y el teclado, el archivo queda mas chico).
- Atajos de teclado globales (funcionan aunque la ventana no tenga el foco):
  - `F9` -> iniciar / detener grabacion.
  - `F10` -> iniciar / detener reproduccion.
  - `Esc` -> parada de emergencia (detiene grabacion y reproduccion).

## Requisitos

- Python 3.8 o superior.
- Libreria [`pynput`](https://pypi.org/project/pynput/) (ver `requirements.txt`).

## Instalacion y ejecucion

### Opcion rapida (Windows)

Doble clic en `ejecutar.bat`. Instala `pynput` si falta y abre la aplicacion.

### Manual

```bash
cd automatizador
py -3 -m pip install -r requirements.txt
py -3 main.py
```

## Como se usa

1. Pulsa **Grabar (F9)** o presiona `F9`. Realiza las acciones que quieras
   automatizar (mouse y teclado).
2. Pulsa **Detener (F9)** o `F9` de nuevo para terminar la grabacion.
3. Pulsa **Guardar como...** para guardarla con un nombre, o usa
   **Reproducir (F10)** / `F10` directamente para probarla.
4. Ajusta **Velocidad** y **Repeticiones** antes de reproducir si lo necesitas.
5. Para volver a usar una macro guardada, selecciona su nombre en la lista
   y pulsa **Cargar**.
6. `Esc` detiene todo en cualquier momento (parada de emergencia).

## Estructura del proyecto

```
automatizador/
  main.py              Interfaz grafica (Tkinter) y atajos globales
  core/
    recorder.py         Captura de eventos de mouse/teclado
    player.py            Reproduccion de eventos grabados
    storage.py            Guardar/cargar/eliminar macros en JSON
  macros/                 Macros guardadas (.json)
  requirements.txt
  ejecutar.bat             Lanzador rapido para Windows
```

## Limitaciones conocidas

- Pensado para Windows (se probo ahi), pero al estar hecho sobre `pynput`
  tambien podria funcionar en macOS/Linux con los permisos de accesibilidad
  correspondientes.
- No incluye edicion visual de pasos, condicionales, ni reconocimiento de
  imagenes en pantalla (funciones avanzadas del Macro Recorder original);
  cubre el flujo basico de grabar -> guardar -> reproducir.
