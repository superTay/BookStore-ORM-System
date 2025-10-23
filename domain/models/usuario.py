"""User domain model using SQLAlchemy ORM.

Represents application users that can place many sales (ventas).
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from config.database import Base


class Usuario(Base):
    """SQLAlchemy model mapped to the `usuarios` table."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)

    ventas = relationship("Venta", back_populates="usuario", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} nombre={self.nombre!r} email={self.email!r}>"
