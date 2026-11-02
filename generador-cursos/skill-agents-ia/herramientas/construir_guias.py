#!/usr/bin/env python3
"""Construye las guías a partir de plantillas.

Cada plantilla (herramientas/plantillas/*.md) puede incluir código REAL:
  {{code:myagent-ai/app/main.py}}            -> archivo del proyecto final
  {{etapa:m05_orchestrator_v1.py|app/application/services/agent_orchestrator.py}}
                                              -> versión por etapas, mostrada con la ruta de destino
  {{demo:m01_primer_llm.py}}                 -> script de demos/
Así el código de la guía nunca se desincroniza del que se probó.
Uso: python3 herramientas/construir_guias.py
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROY = RAIZ / "proyecto"
LANG = {".py": "python", ".txt": "text", ".yml": "yaml", ".ini": "ini", ".md": "markdown", ".example": "bash", ".mako": "python"}


def bloque(ruta_mostrada: str, fuente: Path) -> str:
    texto = fuente.read_text(encoding="utf-8").rstrip("\n")
    lang = LANG.get(fuente.suffix, "text")
    if fuente.name in ("Dockerfile", ".gitignore", ".dockerignore"):
        lang = "dockerfile" if fuente.name == "Dockerfile" else "text"
    if fuente.name == ".env.example":
        lang = "bash"
    return f"📄 **`{ruta_mostrada}`**\n\n```{lang}\n{texto}\n```"


def render(plantilla: str) -> str:
    def code(m): return bloque(m.group(1).split("/", 1)[1], PROY / m.group(1))
    def etapa(m): return bloque(m.group(2), PROY / "etapas" / m.group(1))
    def demo(m): return bloque("demos/" + m.group(1), PROY / "demos" / m.group(1))
    plantilla = re.sub(r"\{\{code:([^}]+)\}\}", code, plantilla)
    plantilla = re.sub(r"\{\{etapa:([^|}]+)\|([^}]+)\}\}", etapa, plantilla)
    return re.sub(r"\{\{demo:([^}]+)\}\}", demo, plantilla)


def main() -> None:
    for tpl in sorted((RAIZ / "herramientas" / "plantillas").glob("*.md")):
        destino_rel = tpl.read_text(encoding="utf-8").split("\n", 1)[0]
        assert destino_rel.startswith("<!-- destino:"), tpl
        destino = RAIZ / destino_rel.removeprefix("<!-- destino:").removesuffix("-->").strip()
        cuerpo = render(tpl.read_text(encoding="utf-8").split("\n", 1)[1])
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(cuerpo, encoding="utf-8")
        print("✔", destino.relative_to(RAIZ))


if __name__ == "__main__":
    main()
