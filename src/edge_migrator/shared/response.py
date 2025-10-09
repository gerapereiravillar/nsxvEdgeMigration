from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

T = TypeVar("T")
#Decorador que genera un constructor con todos los atributos de la clase como argumentos
@dataclass(slots=True)
class Response(Generic[T]):
    """
    Objeto de respuesta estándar para los adapters/puertos.
    - ok: indica si la operación fue exitosa (True) o fallida (False)
    - data: resultado de la operación (cuando ok=True)
    - error: mensaje de error (cuando ok=False)
    """
    ok: bool
    data: Optional[T] = None
    error: Optional[str] = None

    @staticmethod
    def success(data: T) -> "Response[T]":
        return Response(ok=True, data=data)

    @staticmethod
    def failure(msg: str) -> "Response[None]":
        return Response(ok=False, error=msg)
