# Guion de presentación — FootBot: Migración a Simulación (ROS 2 + Gazebo)

> **Duración objetivo:** 5–10 min. Este guion dura **≈ 8–9 min** a ritmo natural.
> **Consejos:** habla pausado, una idea por diapositiva, haz una pequeña pausa al cambiar de slide.
> Los tiempos por diapositiva son orientativos. El texto entre comillas es lo que dices.

---

## Diapositiva 1 — Portada · ≈20 s

"Buenos días. Soy José Daniel Chacón, de la Universidad Nacional Experimental del Táchira. En esta presentación les muestro el componente de **simulación** del proyecto FootBot: cómo llevamos un robot futbolista que funcionaba con un ESP32 en el mundo real hacia un entorno simulado con **ROS 2 y Gazebo**, y por qué lo hicimos."

---

## Diapositiva 2 — Hoja de ruta · ≈20 s

"El recorrido será breve: primero les recuerdo cómo era el robot original; luego explico por qué decidimos simular; cómo trasladamos cada parte del robot físico a ROS 2 y Gazebo; la arquitectura del sistema; las fases del trabajo; los comportamientos autónomos que logramos; la parte de percepción y datos; y cerramos con resultados y trabajo futuro."

---

## Diapositiva 3 — El punto de partida · ≈45 s

"Partimos de un robot ya existente: el **FootBot**, o Auto Soccer Bot. Es un robot futbolista de bajo costo, construido alrededor de un **ESP32-CAM**.

Funcionaba en dos modos. En el modo **manual**, una cámara en el portátil detectaba **gestos de la mano** con MediaPipe, y esos gestos se traducían en comandos de movimiento. En el modo **automático**, el ESP32 transmitía vídeo al portátil, que detectaba el balón con color y con YOLO, y una **máquina de estados** decidía cómo seguirlo.

La idea clave es que la percepción pesada vivía en el portátil, y el robot solo recibía comandos sencillos por una API HTTP. Ese diseño funcionaba, pero tenía un techo."

---

## Diapositiva 4 — ¿Por qué migrar a simulación? · ≈45 s

"¿Por qué dar el salto a la simulación? Porque el banco de pruebas físico nos limitaba: el hardware es frágil y caro, todo depende de la iluminación, y solo teníamos un robot, así que cada prueba era lenta.

La simulación resuelve eso: es **reproducible y determinista** —cada escenario se reinicia idéntico—, es **segura y gratis** de iterar, permite correr **varios escenarios en paralelo**, y nos da la base para comportamientos más ambiciosos.

Y algo importante: **no desechamos lo anterior**. El robot ESP32 sigue como referencia, e incluso conservamos su protocolo HTTP por compatibilidad, mediante un puente."

---

## Diapositiva 5 — Del robot físico al entorno simulado · ≈50 s

"La estrategia fue lo que llamamos *simulation-first*: en vez de portar el firmware, reconstruimos cada capacidad del robot como paquetes de ROS 2.

Esta tabla resume la equivalencia. La tracción diferencial con su driver pasa a ser un **modelo URDF en Gazebo** con un plugin de movimiento. La cámara del ESP32 pasa a ser una **cámara simulada** publicada en un topic. La vieja API HTTP `/move` se mantiene viva con un **puente** que la traduce al topic de velocidad `/cmd_vel`. La visión del portátil se convierte en nodos de percepción, y la máquina de estados pasa al paquete de comportamiento.

En resumen: lo que antes era un stream de vídeo y un POST HTTP, ahora son topics de ROS dentro de un grafo de nodos."

---

## Diapositiva 6 — Arquitectura del sistema · ≈50 s

"El stack es el oficial para esta versión de Ubuntu: **ROS 2 Humble** con **Gazebo Fortress**, unidos por la integración `ros_gz`.

El flujo de datos es siempre el mismo patrón: Gazebo publica los sensores, un **puente** los traduce a topics de ROS, los nodos de percepción generan detecciones, un estimador las convierte en estado, y una máquina de estados decide y publica la velocidad.

Y hay una **regla de oro** que atraviesa todo el diseño: en cada modo, **un solo nodo** puede ser dueño del topic de velocidad. Así evitamos que dos controladores se peleen por el robot. A la derecha ven el robot ya dentro de Gazebo, con su cámara."

---

## Diapositiva 7 — Fases del trabajo · ≈45 s

"El trabajo se hizo en cinco fases.

Primero, los **fundamentos**: el modelo del robot, los mundos y el arranque en Gazebo. Segundo, los **puentes de control**: el topic de velocidad, el puente HTTP compatible con el ESP32, y el control por gestos ahora nativo en ROS. Tercero, la **percepción simulada**: la cámara, la detección de balón por color y la visión con YOLO. Cuarto, el corazón del proyecto: los **comportamientos autónomos**. Y quinto, la **tubería de datos** para entrenar los modelos de visión."

---

## Diapositiva 8 — Control de balón · ≈45 s

"El primer comportamiento es el **control de balón**: que el robot encuentre el balón, se acerque, haga contacto y lo **mantenga** en una zona frontal de control.

Funciona así: la detección por color se convierte en un estado del balón, y una máquina de estados recorre fases como buscar, alinear, aproximar, controlar o recuperar. Un detalle de diseño importante: las llamadas *skills* solo generan comandos de movimiento acotados; **quien decide las transiciones es la máquina de estados**. Eso lo hace predecible y fácil de depurar. A la derecha ven la vista de depuración con el balón detectado."

---

## Diapositiva 8b — Control de balón: cómo lo mantiene centrado · ≈35 s

"Veamos cómo lo hace, de forma sencilla. Lo primero es entender que el robot **no sabe dónde está el balón en el mundo real**: solo lo ve en la imagen de la cámara. Para él, 'tener el balón centrado' es simplemente que el balón aparezca en el **centro del cuadro**.

Entonces hace tres cosas. **Primero**, mide cuánto se desvió el balón del centro y lo convierte en un **ángulo**: si está justo en el medio, el ángulo es cero; si se va hacia un lado, el ángulo crece hacia ese lado. **Segundo**, gira **en proporción a ese error**: si está muy descentrado corrige rápido, y si ya está casi centrado gira suavecito; el signo solo hace que gire hacia el balón. **Y tercero**, no canta victoria al instante: solo da el balón por 'controlado' si se mantiene centrado y cerca durante un ratito. Es un control muy simple, predecible y fácil de depurar."

---

## Diapositiva 9 — Llegar a la portería · ≈55 s

"El segundo comportamiento es más ambicioso: **llevar el balón hasta una portería visible**. Y lo hace **guiado solo por percepción**: nunca usa las posiciones reales que conoce Gazebo; todo sale de la cámara.

Aquí usamos un detector YOLO entrenado para dos clases, balón y portería, que alimenta una máquina de estados que busca el balón, lo controla, busca y se alinea con la portería, y dribla hacia ella.

Tiene dos mecanismos que lo hacen robusto. Uno: una **memoria temporal de la portería**, para cuando esta desaparece del cuadro al acercarse. Y dos: un estado de **empuje final** lento y centrado en el balón. Finalmente, un **árbitro de simulación** detecta el gol y detiene el episodio limpiamente."

---

## Diapositiva 10 — Percepción y datasets · ≈40 s

"Para que todo esto funcione hace falta percepción y datos. La cámara publica las imágenes, y sobre ellas trabajan dos detectores: uno por color para el balón, y YOLO para balón, portería y oponente.

Y detrás hay una **tubería de datos completa y reproducible**: capturamos imágenes de la escena, las etiquetamos en Label Studio, aplicamos aumento de datos, validamos y entrenamos el modelo. A la derecha ven el etiquetado de los objetos de fútbol."

---

## Diapositiva 11 — Resultados y estado actual · ≈40 s

"¿Qué tenemos hoy funcionando? El robot y los mundos en Gazebo, el movimiento por velocidad, el puente HTTP y los gestos, los **dos comportamientos** —control de balón y llegar a la portería—, y todas las herramientas de datos y entrenamiento.

Como verificación objetiva: el paquete de comportamiento compila y su **suite de pruebas pasa: 41 pruebas sin fallos**. A la derecha, el mundo del campo de fútbol completo, que es la base para las siguientes etapas."

---

## Diapositiva 12 — Resultado clave: el remate a corta distancia · ≈45 s

"Pero quiero mostrarles un **resultado clave** —y honesto— del comportamiento de llegar a la portería. Corrimos **cinco episodios**. La buena noticia: el robot controla el balón rápido y de forma estable, en torno a **nueve segundos**. La mala: **solo uno de los cinco terminó en gol**, y ese tardó casi cinco minutos.

En las vistas cenitales —la portería está arriba y el robot sale desde abajo— se ve que el robot y el balón se **quedan estancados justo frente a la portería**. ¿Por qué? Porque cuando el robot se **acerca mucho, la portería ya no cabe entera en la imagen** y el detector YOLO deja de reconocerla de forma continua. La máquina de estados **pierde la referencia** una y otra vez y se va a recuperar y realinear: de hecho, pasa cerca de **un tercio del tiempo** recuperando el balón. Y el estado de respaldo pensado precisamente para esto, *commit to goal*, **no llegó a activarse** en ningún episodio. Esa pérdida de detección a corta distancia es hoy nuestro principal cuello de botella para rematar."

---

## Diapositiva 13 — Trabajo futuro · ≈40 s

"Hacia adelante, la mejora **más inmediata y prioritaria** es resolver esa detección de la portería a corta distancia: reentrenar YOLO con imágenes de portería muy cercana o parcial, detectar los **postes o la línea de meta** en vez de la portería completa, usar una **cámara de mayor campo de visión**, o activar de forma fiable ese **modo de remate por proximidad** guiado por la última posición conocida y la odometría, sin exigir ver la portería todo el tiempo.

Más allá de eso hay tres líneas: **oponentes**, detectar y disputar el balón sin desestabilizar lo que ya funciona; **juego en equipo**, tres robots por bando con roles y espacios de nombres separados; y una línea de **investigación**: árboles de comportamiento, planificación y, cuando tengamos métricas estables, aprendizaje por refuerzo.

El principio rector es siempre el mismo: mantener una base determinista y medible, y añadir táctica solo cuando aporte y sea depurable."

---

## Diapositiva 14 — Conclusiones · ≈30 s

"Para cerrar: la migración convirtió un banco físico frágil en un entorno **reproducible, seguro y escalable**, sin desechar el trabajo previo. Sobre esa base construimos dos comportamientos de fútbol deterministas, con un patrón claro de percepción, estado, decisión y control. Y queda una base sólida para oponentes, equipo y experimentos tácticos."

---

## Diapositiva 15 — Cierre · ≈10 s

"Muchas gracias por su atención. Quedo atento a sus preguntas y comentarios."

---

### Resumen de tiempos
| Bloque | Tiempo aprox. |
|---|---|
| Portada + hoja de ruta | ~0:40 |
| Punto de partida + motivación | ~1:30 |
| Mapeo + arquitectura | ~1:40 |
| Fases + comportamientos (incl. formulación) | ~2:55 |
| Percepción + resultados | ~1:20 |
| Resultado clave (remate a corta distancia) | ~0:45 |
| Futuro + conclusión + cierre | ~1:20 |
| **Total** | **≈ 9:05 min** |

> Para acercarte a **5 min**: acorta los párrafos de las diapositivas 5, 6 y 9 (di solo la primera frase de cada una).
> Para acercarte a **10 min**: añade un ejemplo concreto al hablar de cada comportamiento (8 y 9) y comenta una cifra de la tubería de datos (10).
