"""Sales domain models using SQLAlchemy ORM.

This module defines `Venta` (sale header) and `DetalleVenta` (sale line)
and their relationship. `DetalleVenta` acts as the associative table that
links a `Venta` with one or more `Libro` items and quantities.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from domain.models.usuario import Usuario  # noqa: F401  # ensure class is registered

from config.database import Base


class Venta(Base):
    """Sale header entity.

    Fields
    - id: Primary key.
    - cliente_nombre: Customer name.
    - fecha_venta: Date and time of the sale.
    - total_venta: Calculated total amount.
    """

    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    cliente_nombre: Mapped[str] = mapped_column(String(100), nullable=True)
    fecha_venta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    total_venta: Mapped[float] = mapped_column(Float, nullable=True)

    detalles: Mapped[list["DetalleVenta"]] = relationship(
        "DetalleVenta",
        back_populates="venta",
        cascade="all, delete-orphan",
    )
    usuario = relationship("Usuario", back_populates="ventas")

    def __repr__(self) -> str:
        return f"<Venta id={self.id} cliente={self.cliente_nombre!r} fecha={self.fecha_venta} total={self.total_venta}>"


class DetalleVenta(Base):
    """Sale line (associative table between Venta and Libro)."""

    __tablename__ = "detalle_ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id", ondelete="RESTRICT"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

    venta: Mapped[Venta] = relationship("Venta", back_populates="detalles")
    # Lazy relationship to Libro to avoid circular import at runtime; referenced by string
    libro = relationship("Libro")

    __table_args__ = (
        UniqueConstraint("venta_id", "libro_id", name="uq_detalle_venta_libro"),
    )

    def __repr__(self) -> str:
        return f"<DetalleVenta id={self.id} venta_id={self.venta_id} libro_id={self.libro_id} cantidad={self.cantidad}>"
