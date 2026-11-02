<!-- destino: guia-proyecto-sencillo/01-guia-mi-primer-agente.md -->
# 🌱 Guía paso a paso: tu primer agente de IA (proyecto sencillo y completo)

> ⏱️ Tiempo: 1 hora · 💻 4 archivos de Python · 🆓 Gratis (modelo local con Ollama) · 🎯 Sin conocimientos de IA

## 🎯 Qué vas a construir

Un **Asistente de tareas** que entiende español normal y maneja una lista de pendientes:

```text
Tú: Agrega la tarea comprar leche
Agente: Listo, agregué "comprar leche".
Tú: ¿Qué tareas tengo?
Agente: Tienes: 1. comprar leche
Tú: Completa la tarea 1
Agente: Hecho, la tarea 1 está completada.
```

No le programas esas frases. **El modelo decide** qué función usar. Eso es un agente.

## 🗺️ El plan en una imagen

```mermaid
flowchart LR
    T["👤 Tú escribes"] --> C["chat.py<br/>(la terminal)"]
    C --> A["agente.py<br/>(el ciclo)"]
    A <--> M["🧠 Modelo<br/>(Ollama)"]
    A --> H["herramientas.py<br/>(las manos)"]
    H --> F[("tareas.json")]
```

| Archivo | Para qué sirve | Analogía |
|---|---|---|
| `herramientas.py` | Funciones que hacen cosas (guardar tareas) | Las manos |
| `agente.py` | El ciclo: pensar → usar herramienta → responder | El jefe |
| `chat.py` | Conversar desde la terminal | La ventanilla |
| `test_agente.py` | Comprobar que todo funciona sin modelo | El inspector |

---

## 🧰 Paso 0 — Preparar el computador (Ubuntu)

**0.1** Instala Ollama y descarga un modelo pequeño:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
```

✅ *Comprueba:* `ollama list` muestra `llama3.2`.

**0.2** Revisa tu Python (debe ser 3.11 o superior):

```bash
python3 --version
```

Si dice 3.10, instala una versión nueva con `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv python install 3.12
```

---

## 📁 Paso 1 — Crear la carpeta y el entorno

```bash
mkdir ~/mini-agente && cd ~/mini-agente
uv venv --python 3.12 .venv          # o: python3 -m venv .venv  (si ya tienes 3.11+)
source .venv/bin/activate
```

✅ *Comprueba:* ves `(.venv)` al inicio de la línea.

> 💡 Cada vez que abras una terminal nueva, entra a la carpeta y ejecuta `source .venv/bin/activate`.

---

## 📦 Paso 2 — Instalar lo necesario

Crea el archivo `requirements.txt` (es la lista de compras):

{{code:mini-agente/requirements.txt}}

Instala:

```bash
uv pip install -r requirements.txt     # o: pip install -r requirements.txt
```

✅ *Comprueba:* `python -c "import ollama; print('ok')"` imprime `ok`.

---

## ✋ Paso 3 — Las manos: `herramientas.py`

Aquí escribes **funciones normales de Python**. Nada de IA todavía.

{{code:mini-agente/herramientas.py}}

**¿Qué hay aquí?**

| Parte | Qué hace |
|---|---|
| `_leer` / `_guardar` | Leen y escriben `tareas.json` |
| `agregar_tarea`, `listar_tareas`, `completar_tarea` | Las 3 cosas que el agente sabrá hacer |
| `TARJETAS` | La "ficha" de cada función: nombre, para qué sirve y qué datos recibe. **El modelo solo lee esto**, nunca ve tu código |
| `FUNCIONES` | Un diccionario `nombre → función`. Solo lo que esté aquí se puede ejecutar |
| `int(id)` | El modelo a veces manda `"1"` (texto) en vez de `1`. Lo arreglamos aquí |

✅ **Prueba rápida** (sin IA):

```bash
python -c "
import herramientas as h
print(h.agregar_tarea('Probar'))
print(h.listar_tareas())
"
rm tareas.json
```

Debe imprimir `Tarea 1 creada: Probar` y `1. [ ] Probar`.

---

## 🧠 Paso 4 — El cerebro de control: `agente.py`

{{code:mini-agente/agente.py}}

**Léelo con calma. Es el corazón del curso.**

```mermaid
sequenceDiagram
    participant Tú
    participant Agente as agente.py
    participant Modelo
    participant Mano as herramientas.py
    Tú->>Agente: "Agrega la tarea comprar leche"
    Agente->>Modelo: reglas + historia + tarjetas
    Modelo-->>Agente: "Quiero usar agregar_tarea(titulo='comprar leche')"
    Note over Modelo,Agente: El modelo SOLO PIDE
    Agente->>Mano: agregar_tarea('comprar leche')
    Mano-->>Agente: "Tarea 1 creada"
    Agente->>Modelo: historia + resultado
    Modelo-->>Agente: "Listo, la agregué"
    Agente-->>Tú: "Listo, la agregué"
```

| Línea | Qué hace |
|---|---|
| `REGLAS` | Instrucciones fijas. Mira la última: *"nunca con JSON"* (la agregamos porque el modelo pequeño a veces respondía con JSON en vez de una frase) |
| `MAX_VUELTAS = 5` | **Freno de seguridad**: si el modelo se confunde, no repite para siempre |
| `ejecutar(...)` | Ejecuta la función **solo si existe** en `FUNCIONES`. Los errores se devuelven como texto para que el modelo los lea |
| `for _ in range(MAX_VUELTAS)` | El ciclo del agente |
| `historia.append(respuesta)` | Guardamos lo que dijo el modelo (así "recuerda") |
| `if not respuesta.tool_calls` | Si no pidió herramientas, ya terminó: devolvemos su texto |
| `for pedido in ...` | Si pidió herramientas, **nosotros las ejecutamos** y le devolvemos el resultado con rol `tool` |

> 🔑 **Idea clave:** el modelo *pide*, tu programa *ejecuta*. Por eso puedes ponerle límites.

---

## 💬 Paso 5 — La ventanilla: `chat.py`

{{code:mini-agente/chat.py}}

| Parte | Qué hace |
|---|---|
| `Client(host=...)` | Se conecta a Ollama (puerto 11434) |
| `historia = []` | La memoria de la conversación (vive mientras el programa esté abierto) |
| `while True` | Repite: leer lo que escribes → preguntar al agente → mostrar |

---

## ▶️ Paso 6 — ¡Probarlo!

Asegúrate de que Ollama esté activo (`ollama list` debe responder) y ejecuta:

```bash
python chat.py
```

Escribe estas frases, una por una:

```text
Agrega la tarea comprar leche
Agrega la tarea llamar al médico
¿Qué tareas tengo?
Completa la tarea 1
¿Qué tareas tengo?
salir
```

**Resultado esperado** (las palabras exactas cambian; las líneas con 🔧 son lo importante):

```text
Tú:    🔧 agregar_tarea({'titulo': 'comprar leche'}) -> Tarea 1 creada: comprar leche
Agente: Tareas pendientes: comprar leche

Tú:    🔧 agregar_tarea({'titulo': 'llamar al médico'}) -> Tarea 2 creada: llamar al médico
...
Tú:    🔧 completar_tarea({'id': '1'}) -> Tarea 1 completada.
Agente: Tareas pendientes: llamar al médico

Tú:    🔧 listar_tareas({}) -> 1. [x] comprar leche
                                2. [ ] llamar al médico
```

Abre `tareas.json` y verás tus tareas guardadas. Si cierras y vuelves a abrir `chat.py`, **siguen ahí**.

> 🔬 **Nota honesta:** el modelo pequeño a veces responde con frases raras (por ejemplo, contestar solo "Tareas pendientes: ..." cuando agregaste una tarea). Lo que **sí** debe ser correcto son las líneas 🔧 y el archivo `tareas.json`. Con un modelo más grande las frases mejoran.

---

## 🧪 Paso 7 — Pruebas automáticas (sin modelo)

Una buena práctica: probar tu código **sin depender de la IA**. Usamos un "modelo de mentira" que responde lo que nosotros le decimos.

{{code:mini-agente/test_agente.py}}

```bash
pytest -v
```

**Resultado esperado:** `6 passed`.

| Prueba | Qué comprueba |
|---|---|
| `test_agregar_y_listar` | Las herramientas guardan y leen bien |
| `test_completar_acepta_id_como_texto` | `"1"` funciona igual que `1` |
| `test_completar_tarea_inexistente` | Un error claro, sin romper |
| `test_el_agente_usa_la_herramienta...` | El ciclo completo, con el cliente falso |
| `test_herramienta_inexistente...` | Una herramienta inventada se rechaza |
| `test_limite_de_vueltas` | El freno funciona aunque el modelo "se vuelva loco" |

> 🧪 `tmp_path` y `monkeypatch` hacen que las pruebas usen una carpeta temporal, así **no tocan tu `tareas.json` real**.

---

## 🛠️ Si algo falla

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError: ollama` | Entorno sin activar o sin instalar | `source .venv/bin/activate` y repite el Paso 2 |
| `ConnectError` / "Failed to connect to Ollama" | Ollama no está corriendo | `ollama serve` (o `sudo systemctl start ollama`) |
| `model 'llama3.2' not found` | No descargaste el modelo | `ollama pull llama3.2` |
| El agente no usa herramientas | Modelo pequeño distraído | Repite con frases claras: "Agrega la tarea ..." |
| Las tareas "desaparecen" | Ejecutas desde otra carpeta | `tareas.json` se crea donde ejecutas `python chat.py`; entra siempre a `~/mini-agente` |
| `ModuleNotFoundError: agente` en pytest | Ejecutas pytest desde otra carpeta | Hazlo dentro de `~/mini-agente` |

---

## 🏋️ Ejercicios (para practicar)

1. **Borrar tareas.** Agrega la herramienta `borrar_tarea(id)`. *Pasos:* escribe la función, agrégala a `TARJETAS` y a `FUNCIONES`, y crea su prueba.
2. **Tareas con fecha.** Agrega un campo `fecha` opcional a `agregar_tarea`. ¿Qué cambias en la tarjeta?
3. **Cambia el modelo.** Pon `MODELO = "llama3"` en `chat.py` y compara respuestas.
4. **Cambia la personalidad.** Edita `REGLAS` para que el asistente hable como pirata. ¿Sigue usando las herramientas bien?
5. **Rompe el freno.** Pon `MAX_VUELTAS = 1` y pide "agrega una tarea". ¿Qué pasa y por qué?
6. **Seguridad.** Pide: "borra todos mis archivos". ¿Qué hace el agente? ¿Qué parte del código lo protege? *(Pista: `FUNCIONES`.)*

---

## ✅ Qué aprendiste

- Un **agente** es un ciclo: el modelo decide, tu programa ejecuta, el resultado vuelve al modelo.
- Las **herramientas** son funciones normales con una "tarjeta" que el modelo puede leer.
- El **límite de vueltas** y el diccionario de **funciones permitidas** son tus guardarraíles.
- Se puede **probar** un agente sin IA usando un cliente falso.

## ➡️ Siguiente paso

Este proyecto es el MyAgent AI del curso **en miniatura**: todo está en pocos archivos. En el curso completo ves lo mismo con arquitectura profesional (varios proveedores de IA, base de datos, RAG, seguridad y Docker).

👉 [Volver al índice del curso](../README.md) · [Módulo 1](../modulo-01-fundamentos/01-guia-fundamentos.md) · [Módulo 5: el orquestador](../modulo-05-orchestrator/01-guia-orchestrator.md)
