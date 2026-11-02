"""El cerebro de control: el ciclo del agente."""
from herramientas import FUNCIONES, TARJETAS

REGLAS = (
    "Eres un asistente de tareas. Responde en español, corto y claro. "
    "Para ver, crear o completar tareas USA las herramientas; no inventes tareas. "
    "Cuando termines, contesta con una frase normal, nunca con JSON."
)
MAX_VUELTAS = 5


def ejecutar(nombre: str, argumentos: dict) -> str:
    """Ejecuta la herramienta pedida, pero solo si existe. Los errores vuelven como texto."""
    if nombre not in FUNCIONES:
        return f"ERROR: la herramienta '{nombre}' no existe."
    try:
        return FUNCIONES[nombre](**argumentos)
    except TypeError as e:
        return f"ERROR: argumentos incorrectos ({e})."


def preguntar(cliente, modelo: str, historia: list[dict], texto: str) -> str:
    historia.append({"role": "user", "content": texto})
    for _ in range(MAX_VUELTAS):
        mensajes = [{"role": "system", "content": REGLAS}] + historia
        respuesta = cliente.chat(model=modelo, messages=mensajes, tools=TARJETAS).message
        historia.append(respuesta)
        if not respuesta.tool_calls:
            return respuesta.content
        for pedido in respuesta.tool_calls:
            resultado = ejecutar(pedido.function.name, dict(pedido.function.arguments))
            print(f"   🔧 {pedido.function.name}({dict(pedido.function.arguments)}) -> {resultado}")
            historia.append({"role": "tool", "tool_name": pedido.function.name, "content": resultado})
    return "Llegué al límite de pasos sin terminar."
