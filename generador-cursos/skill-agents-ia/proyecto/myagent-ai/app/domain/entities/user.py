from dataclasses import dataclass


@dataclass
class User:
    """Quien usa la plataforma. El rol decide qué puede hacer."""

    id: str
    role: str = "user"  # "admin" o "user"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
