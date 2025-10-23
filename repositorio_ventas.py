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

                # Validate stock and decrement atomically within the transaction
                current_stock = int(libro.stock or 0)
                if current_stock < cantidad:
                    raise ValueError(
                        f"Insufficient stock for libro_id={libro_id}: have {current_stock}, need {cantidad}"
                    )
                libro.stock = current_stock - cantidad

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

    def actualizar_pedido(self, venta_id: int, items: Sequence[tuple[int, int]]) -> Optional[Venta]:
        """Replace a sale's items atomically, with stock reconciliation.

        Steps
        - Load current Venta and its details.
        - Restore stock from current details.
        - Validate and apply new items (decrement stock).
        - Recompute total_venta and persist.
        """
        session = self._session()
        try:
            venta = session.get(Venta, venta_id)
            if not venta:
                return None

            # Restore stock from existing details
            for d in list(venta.detalles):
                libro = session.get(Libro, d.libro_id)
                if libro:
                    libro.stock = int(libro.stock or 0) + int(d.cantidad or 0)
            # Clear existing details (delete-orphan via relationship)
            venta.detalles.clear()
            session.flush()

            # Aggregate duplicate items (libro_id) in the new payload
            aggregated = {}
            for libro_id, cantidad in items:
                if cantidad is None or cantidad <= 0:
                    raise ValueError(f"Invalid quantity for libro_id={libro_id}: {cantidad}")
                aggregated[libro_id] = aggregated.get(libro_id, 0) + int(cantidad)

            total = 0.0
            for libro_id, cantidad in aggregated.items():
                libro = session.get(Libro, libro_id)
                if not libro:
                    raise ValueError(f"Libro with id={libro_id} not found")
                current_stock = int(libro.stock or 0)
                if current_stock < cantidad:
                    raise ValueError(
                        f"Insufficient stock for libro_id={libro_id}: have {current_stock}, need {cantidad}"
                    )
                libro.stock = current_stock - cantidad
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
