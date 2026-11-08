# Automatizador

Clon, hecho en Python, de la idea de **Macro Recorder** (Martels Media):
graba lo que haces con el mouse y el teclado y lo vuelve a reproducir
exactamente igual, respetando los tiempos originales. Ademas incluye un
**panel de acciones** para armar o editar una macro a mano, accion por
accion, igual que en el programa original.

## Que incluye

- Grabacion de movimientos de mouse, clics (izq/der/medio), rueda del mouse
  y pulsaciones de teclado, con el tiempo de espera real entre cada una.
- **Panel de acciones**: lista completa de la macro (grabada o manual) con
  columnas de retraso, tipo y detalle. Permite:
  - **Agregar** una accion nueva eligiendo su tipo de una lista.
  - **Editar** (doble clic o boton "Editar...") cualquier accion existente.
  - **Duplicar**, **Eliminar**, **Subir/Bajar** (reordenar) y **Vaciar** la lista.
- Tipos de accion disponibles para agregar manualmente:
  - **Mover mouse** a una posicion X, Y.
  - **Clic de mouse** (izquierdo/derecho/central; clic, presionar o soltar;
    con opcion de doble clic).
  - **Arrastrar mouse** (de un punto a otro, con boton y duracion).
  - **Rueda del mouse** (desplazamiento horizontal/vertical).
  - **Presionar tecla** / **Tecla abajo (mantener)** / **Tecla arriba (soltar)**,
    eligiendo la tecla de una lista de teclas especiales, escribiendo un
    caracter, o con el boton **Capturar...** (detecta la siguiente tecla
    que presiones).
  - **Escribir texto** (una frase completa, con intervalo entre teclas).
  - **Esperar / pausa** (una espera explicita, en segundos).
  - **Ejecutar programa** (abre un .exe u otro archivo, con argumentos
    opcionales).
  - **Abrir pagina web** (una URL en el navegador por defecto).
  - **Mostrar mensaje** (un cuadro de dialogo con titulo y texto).
  - **Capturar imagen de pantalla** (guarda una captura, de toda la pantalla
    o de una region, en un archivo; incluye un selector de region
    interactivo y un boton para probarla).
  - **Buscar imagen en pantalla** (busca una imagen de referencia en toda la
    pantalla o en una region, con nivel de confianza configurable):
    - **Si se encuentra**: ejecuta una accion de mouse (clic, doble clic,
      clic derecho o solo mover el mouse) en el punto encontrado, con un
      desplazamiento (offset) opcional.
    - **Si no se encuentra**: espera una cantidad de segundos y, si se
      indica un numero de paso mayor a 0, salta a ese paso de la lista de
      acciones (permite reintentar el mismo bloque hasta encontrar la
      imagen).
- Reproduccion fiel a los tiempos grabados o definidos a mano, con control de:
  - **Velocidad** (0.1x a 10x).
  - **Repeticiones** (un numero fijo, o 0 = bucle infinito).
- Guardar y cargar macros como archivos `.json` dentro de `macros/`
  (botones **Nueva macro**, **Guardar**, **Guardar como...**, **Cargar**,
  **Eliminar**, **Refrescar**). Las macros guardadas con la version anterior
  del programa se siguen pudiendo abrir (se migran automaticamente al
  formato nuevo).
- Casilla para activar/desactivar la grabacion de movimientos del mouse
  (si solo te interesan los clics y el teclado, el archivo queda mas chico).
- Atajos de teclado globales (funcionan aunque la ventana no tenga el foco):
  - `F9` -> iniciar / detener grabacion.
  - `F10` -> iniciar / detener reproduccion.
  - `Esc` -> parada de emergencia (detiene grabacion y reproduccion).

## Requisitos

- Python 3.8 o superior.
- Libreria [`pynput`](https://pypi.org/project/pynput/) (ver `requirements.txt`).
- Para **Capturar imagen de pantalla** y **Buscar imagen en pantalla**:
  [`pyautogui`](https://pypi.org/project/PyAutoGUI/) y `Pillow` (incluidas en
  `requirements.txt`). `opencv-python` es opcional y habilita la busqueda
  "por confianza" (coincidencia aproximada); sin ella, la busqueda de imagen
  es por coincidencia exacta de pixeles.

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

### Grabando una macro

1. Pulsa **Grabar (F9)** o presiona `F9`. Realiza las acciones que quieras
   automatizar (mouse y teclado).
2. Pulsa **Detener (F9)** o `F9` de nuevo para terminar la grabacion: las
   acciones grabadas aparecen en el **panel de acciones**.
3. Ajusta, reordena o agrega acciones manualmente si lo necesitas (ver abajo).
4. Pulsa **Guardar** o **Guardar como...** para guardarla con un nombre, o
   usa **Reproducir (F10)** / `F10` directamente para probarla.

### Armando una macro a mano

1. Pulsa **Nueva macro** (o parte de una ya cargada).
2. En el **panel de acciones**, pulsa **Agregar...**, elige el tipo de
   accion (mover mouse, clic, arrastrar, rueda, tecla, texto, pausa,
   ejecutar programa, abrir URL, mostrar mensaje) y completa sus datos.
3. La accion se inserta despues de la seleccionada (o al final si no hay
   ninguna seleccionada). Usa **Subir/Bajar** para reordenar, **Editar...**
   para corregirla o **Duplicar** para repetirla.
4. Ajusta **Velocidad** y **Repeticiones** y pulsa **Reproducir (F10)**
   para probar la macro.

### Otras acciones

- Para volver a usar una macro guardada, selecciona su nombre en la lista
  de la izquierda y pulsa **Cargar**.
- `Esc` detiene todo en cualquier momento (parada de emergencia).

## Estructura del proyecto

```
automatizador/
  main.py                   Interfaz grafica (Tkinter), panel de acciones y atajos globales
  core/
    recorder.py              Captura de eventos de mouse/teclado (con retraso relativo)
    player.py                Reproduccion de todos los tipos de accion
    actions.py                Catalogo de tipos de accion y su descripcion en pantalla
    action_dialog.py          Dialogo para agregar/editar una accion a mano
    keys.py                   Utilidades para serializar y mostrar teclas
    image_search.py            Captura de pantalla y busqueda de imagenes
    storage.py                 Guardar/cargar/eliminar macros en JSON (con migracion)
  macros/                      Macros guardadas (.json)
  images/                       Capturas e imagenes de referencia (opcional)
  requirements.txt
  ejecutar.bat                  Lanzador rapido para Windows
```

## Limitaciones conocidas

- Pensado para Windows (se probo ahi), pero al estar hecho sobre `pynput`
  tambien podria funcionar en macOS/Linux con los permisos de accesibilidad
  correspondientes.
- No incluye variables ni condicionales genericos (funciones avanzadas de
  versiones de pago del Macro Recorder original); si incluye busqueda de
  imagenes en pantalla con una rama "si se encuentra / si no se encuentra"
  (ver **Buscar imagen en pantalla** mas arriba).
