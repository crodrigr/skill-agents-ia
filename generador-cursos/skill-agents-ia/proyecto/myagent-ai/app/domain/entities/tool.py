from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpec:
    """La 'tarjeta' de una herramienta: lo que el modelo puede leer.

    `parameters` es un JSON Schema. `sensitive=True` exige aprobación humana.
    """

    name: str
    description: str
    parameters: dict
    sensitive: bool = False
