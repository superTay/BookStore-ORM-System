"""Persistence layer (Repository) for Venta and DetalleVenta operations.

Encapsulates creation of sales (Venta) with their line items (DetalleVenta),
listing, retrieval, and basic deletion, handling sessions and transactions
consistently.
"""

from typing import Iterable, Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal
from venta import Venta, DetalleVenta
from libro import Libro


class RepositorioVentas:
    """Repository dedicated to sales persistence (Venta/DetalleVenta)."""

    def _session(self):
        return SessionLocal()

    def crear_venta(
        self,
        cliente_nombre: Optional[str],
        items: Sequence[tuple[int, int]],
    ) -> Venta:
        """Create a Venta with its DetalleVenta rows in a single transaction.

        Parameters
        - cliente_nombre: Optional customer name.
        - items: sequence of tuples (libro_id, cantidad)

        Behavior
        - Validates each libro_id exists and cantidad > 0.
        - Computes total_venta as sum(cantidad * libro.precio) ignoring None prices as 0.0.
        - Persists Venta and DetalleVenta rows atomically.
        """
        session = self._session()
        try:
            venta = Venta(cliente_nombre=cliente_nombre)
            session.add(venta)
            total = 0.0

            for libro_id, cantidad in items:
                if cantidad is None or cantidad <= 0:
                    raise ValueError(f"Invalid quantity for libro_id={libro_id}: {cantidad}")

                libro = session.get(Libro, libro_id)
                if not libro:
                    raise ValueError(f"Libro with id={libro_id} not found")

                precio = float(libro.precio or 0.0)
                total += precio * cantidad

                detalle = DetalleVenta(venta=venta, libro_id=libro_id, cantidad=cantidad)
                session.add(detalle)

            venta.total_venta = total
            session.commit()
            session.refresh(venta)
            return venta
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def obtener_venta_por_id(self, venta_id: int) -> Optional[Venta]:
        """Return a Venta by id, or None if not found."""
        with SessionLocal() as session:
            return session.get(Venta, venta_id)

    def listar_ventas(self) -> Iterable[Venta]:
        """List all ventas ordered by most recent first."""
        with SessionLocal() as session:
            stmt = select(Venta).order_by(Venta.fecha_venta.desc())
            return list(session.execute(stmt).scalars().all())

    def eliminar_venta(self, venta_id: int) -> bool:
        """Delete a sale by id (cascades to DetalleVenta)."""
        session = self._session()
        try:
            venta = session.get(Venta, venta_id)
            if not venta:
                return False
            session.delete(venta)
            session.commit()
            return True
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

