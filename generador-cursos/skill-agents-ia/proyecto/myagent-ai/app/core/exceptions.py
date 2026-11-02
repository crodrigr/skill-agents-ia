class MyAgentError(Exception):
    """Error base de la plataforma."""


class LLMError(MyAgentError):
    """El modelo de lenguaje falló o no respondió."""


class ToolError(MyAgentError):
    """Una herramienta falló o no está permitida."""


class NotFoundError(MyAgentError):
    """No se encontró lo pedido (agente, sesión...)."""


class PermissionDeniedError(MyAgentError):
    """El usuario no tiene permiso para hacer esto."""
