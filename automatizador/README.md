# Automatizador

Clon, hecho en Python, de la idea de **Macro Recorder** (Martels Media):
graba lo que haces con el mouse y el teclado y lo vuelve a reproducir
exactamente igual, respetando los tiempos originales. Ademas incluye un
**panel de acciones** para armar o editar una macro a mano, accion por
accion, igual que en el programa original.

## Que incluye

- Interfaz grafica con tema moderno (colores, iconos en los botones, filas
  alternadas en la lista de acciones, barra de progreso de reproduccion,
  buscador para filtrar las macros guardadas y menu superior con todas las
  acciones disponibles).
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
  - **Buscar texto en pantalla (OCR)** (busca un texto, por reconocimiento
    optico de caracteres, en toda la pantalla o en una region; con opcion
    de distinguir mayusculas/minusculas e idioma del OCR). Tiene las
    mismas opciones que **Buscar imagen en pantalla**:
    - **Si se encuentra**: ejecuta una accion de mouse (clic, doble clic,
      clic derecho o solo mover el mouse) en el punto encontrado, con un
      desplazamiento (offset) opcional.
    - **Si no se encuentra**: espera una cantidad de segundos y, si se
      indica un numero de paso mayor a 0, salta a ese paso de la lista de
      acciones.
- Reproduccion fiel a los tiempos grabados o definidos a mano, con control de:
  - **Velocidad** (0.1x a 10x).
  - **Repeticiones** (un numero fijo, o 0 = bucle infinito).
  - **Ejecutar desde la accion seleccionada**: reproduce solo desde el
    paso elegido en el panel de acciones hasta el final, sin tocar la
    reproduccion completa de siempre (ver **Como se usa**).
  - **Ejecutar una macro guardada en segundo plano**: la corre en un
    proceso aparte, sin ventana, independiente de la ventana principal
    (y tambien disponible por linea de comandos con `--background`, ver
    **Como se usa**).
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
- Para **Buscar texto en pantalla (OCR)**: libreria
  [`pytesseract`](https://pypi.org/project/pytesseract/) (incluida en
  `requirements.txt`) **y** el motor
  [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) instalado en
  el sistema (no es un paquete de Python; hay que instalarlo aparte, por
  ejemplo con su instalador para Windows).

## Instalacion y ejecucion

### Opcion rapida (Windows)

Doble clic en `ejecutar.bat`. Instala `pynput` si falta y abre la aplicacion.

### Manual

```bash
cd automatizador
py -3 -m pip install -r requirements.txt
py -3 main.py
```

> `main.py` tambien acepta `--background NOMBRE_MACRO [--speed N] [--repeat N]`
> para ejecutar una macro guardada sin abrir la interfaz grafica (ver
> **Ejecutar una macro guardada en segundo plano** en **Como se usa**).

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

### Ejecutar desde la accion seleccionada

Permite saltarse al principio de la macro y empezar la reproduccion justo
en el paso que elijas, sin tener que borrar ni reordenar nada:

1. Carga o arma la macro como siempre y, en el **panel de acciones**,
   selecciona (con un clic) la fila desde la que quieres empezar.
2. Pulsa **"⏩ Ejecutar desde aqui"** (abajo a la derecha del panel de
   acciones) o el menu **Ejecucion -> Ejecutar desde la accion
   seleccionada**.
3. Se reproducen, respetando **Velocidad** y **Repeticiones**, todas las
   acciones desde la seleccionada hasta el final de la lista. La barra de
   progreso y el boton **Reproducir / Detener (F10)** funcionan igual que
   con una reproduccion normal, asi que `F10` o el boton de reproduccion
   tambien la detienen.

> Esto no reemplaza a **Reproducir (F10)**: ese boton sigue reproduciendo
> la macro completa de siempre; "Ejecutar desde aqui" es una forma extra
> de arrancar a mitad de camino (util para probar solo el tramo final de
> una macro larga sin esperar a que se repita todo desde el principio).

### Ejecutar una macro guardada en segundo plano

Lanza una macro guardada como un **proceso aparte, sin ventana**, que
sigue corriendo aunque cierres (o sigas usando) la ventana principal del
Automatizador. Util para dejar una macro trabajando mientras usas la
compu para otra cosa, o para lanzarla desde el Programador de tareas de
Windows sin que aparezca ninguna interfaz.

**Desde la interfaz grafica:**

1. En la lista **"Macros guardadas"**, selecciona la macro que quieres
   correr en segundo plano (no hace falta cargarla en el panel de
   acciones).
2. Ajusta, si queres, **Velocidad** y **Repeticiones** (se usan los
   mismos valores que ves en el panel de **Reproduccion**).
3. Pulsa **"🏃 Ejecutar en 2do plano"** (debajo de la lista de macros) o
   el menu **Ejecucion -> Ejecutar macro seleccionada en 2do plano**.
4. El Automatizador abre un proceso de Python independiente que carga esa
   macro y la reproduce sin mostrar ninguna ventana; la barra de estado
   confirma que el proceso se inicio. Podes seguir usando la aplicacion
   (grabar, editar, reproducir otra macro) mientras esa reproduccion
   corre por su cuenta.

**Desde la linea de comandos** (por ejemplo, para programarla con el
Programador de tareas de Windows), sin abrir la interfaz grafica:

```bash
cd automatizador
py -3 main.py --background "NombreDeLaMacro"
py -3 main.py --background "NombreDeLaMacro" --speed 1.5 --repeat 0
```

- `--background NOMBRE` (obligatorio para este modo): nombre de la macro
  guardada en `macros/` (el mismo que ves en la lista de la izquierda).
- `--speed` (opcional, por defecto `1.0`): multiplicador de velocidad.
- `--repeat` (opcional, por defecto `1`): numero de repeticiones; `0` =
  bucle infinito (se detiene matando el proceso).

El proceso en segundo plano no abre ninguna ventana (ni de la
aplicacion ni consola, cuando se lanza desde la interfaz grafica),
imprime su progreso por la salida estandar cuando se ejecuta desde una
consola visible, y termina solo cuando la macro finaliza.

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
    image_search.py            Captura de pantalla y busqueda de imagenes/texto (OCR)
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
  imagenes y de texto (OCR) en pantalla con una rama "si se encuentra / si
  no se encuentra" (ver **Buscar imagen en pantalla** y **Buscar texto en
  pantalla (OCR)** mas arriba).
