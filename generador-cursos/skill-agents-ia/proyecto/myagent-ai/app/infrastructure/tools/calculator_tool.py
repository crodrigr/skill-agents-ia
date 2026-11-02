import ast
import operator

from app.core.exceptions import ToolError
from app.domain.entities.tool import ToolSpec
from app.domain.ports.tool_port import ToolPort

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval(nodo: ast.AST) -> float:
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPS:
        if isinstance(nodo.op, ast.Pow):
            exp = _eval(nodo.right)
            if abs(exp) > 100:
                raise ToolError("Exponente demasiado grande.")
        return _OPS[type(nodo.op)](_eval(nodo.left), _eval(nodo.right))
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in _OPS:
        return _OPS[type(nodo.op)](_eval(nodo.operand))
    raise ToolError("Solo se permiten números y + - * / **.")


class CalculatorTool(ToolPort):
    """Calcula expresiones SIN usar eval(): solo recorre un árbol permitido."""

    spec = ToolSpec(
        name="calculator",
        description="Calcula una expresión matemática con números y + - * / **. Úsala solo cuando la pregunta sea una cuenta.",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "La operación a calcular"}},
            "required": ["expression"],
        },
    )

    async def run(self, expression: str) -> str:
        try:
            return str(_eval(ast.parse(expression, mode="eval").body))
        except ZeroDivisionError as e:
            raise ToolError("No se puede dividir entre cero.") from e
        except SyntaxError as e:
            raise ToolError("Expresión inválida.") from e
