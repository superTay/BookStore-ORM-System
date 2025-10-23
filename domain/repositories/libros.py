"""Persistence layer (Repository) for Libro CRUD operations.

Encapsulates database-session management and common operations over the
Libro model to keep application code decoupled from persistence details.
"""

from contextlib import contextmanager
from typing import Iterable, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from config.database import SessionLocal
from domain.models.libro import Libro


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations.

    Commits on success; rolls back on exception; always closes the session.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class RepositorioLibros:
    """Repository for managing Libro entities with safe session handling."""

    def agregar_libro(
        self,
        titulo: str,
        autor: str,
        isbn: Optional[str] = None,
        stock: Optional[int] = None,
        precio: Optional[float] = None,
    ) -> Libro:
        """Create and persist a new Libro.

        Raises IntegrityError if `isbn` duplicates an existing record.
        Returns the persisted Libro (refreshed with DB-generated fields).
        """
        with session_scope() as session:
            libro = Libro(titulo=titulo, autor=autor, isbn=isbn, stock=stock, precio=precio)
            session.add(libro)
            try:
                session.flush()  # to get PK and detect integrity issues early
            except IntegrityError as e:
                # Re-raise with clearer context for caller
                raise IntegrityError(
                    statement=e.statement,
                    params=e.params,
                    orig=e.orig,
                )
            session.refresh(libro)
            return libro

    def listar_libros(self) -> Iterable[Libro]:
        """Return an iterable of all Libro records ordered by id."""
        with session_scope() as session:
            rows = session.query(Libro).order_by(Libro.id.asc()).all()
            # Eagerly load scalar attributes to avoid DetachedInstanceError after session closes
            for r in rows:
                _ = (r.id, r.titulo, r.autor, r.isbn, r.stock, r.precio)
            return list(rows)

    def actualizar_stock_libro(self, libro_id: int, nuevo_stock: int) -> Optional[Libro]:
        """Update the stock of a Libro by id; returns the updated entity or None.

        Rolls back and raises SQLAlchemyError on unexpected DB errors.
        """
        with session_scope() as session:
            libro: Optional[Libro] = session.get(Libro, libro_id)
            if not libro:
                return None
            libro.stock = nuevo_stock
            try:
                session.flush()
            except SQLAlchemyError:
                raise
            session.refresh(libro)
            return libro

    def obtener_libro_por_id(self, libro_id: int) -> Optional[Libro]:
        """Fetch a single Libro by its primary key; returns None if missing."""
        with session_scope() as session:
            return session.get(Libro, libro_id)

    def eliminar_libro(self, libro_id: int) -> bool:
        """Delete a Libro by id.

        Returns True if a row was deleted; False if the id did not exist.
        """
        with session_scope() as session:
            libro: Optional[Libro] = session.get(Libro, libro_id)
            if not libro:
                return False
            session.delete(libro)
            # flush to ensure deletion happens within the scope
            session.flush()
            return True

    def actualizar_precios(
        self,
        autor: Optional[str] = None,
        ids: Optional[Iterable[int]] = None,
        min_precio: Optional[float] = None,
        max_precio: Optional[float] = None,
        nuevo_precio: Optional[float] = None,
        factor: Optional[float] = None,
    ) -> int:
        """Bulk update book prices based on filters.

        - If both `nuevo_precio` and `factor` are provided, `nuevo_precio` takes precedence.
        - If neither is provided, raises ValueError.

        Returns the number of affected rows.
        """
        if nuevo_precio is None and factor is None:
            raise ValueError("Provide either 'nuevo_precio' or 'factor'.")

        with session_scope() as session:
            q = session.query(Libro)
            if autor is not None:
                q = q.filter(Libro.autor == autor)
            if ids is not None:
                q = q.filter(Libro.id.in_(list(ids)))
            if min_precio is not None:
                q = q.filter(Libro.precio >= min_precio)
            if max_precio is not None:
                q = q.filter(Libro.precio <= max_precio)

            libros = q.all()
            count = 0
            for l in libros:
                if nuevo_precio is not None:
                    l.precio = float(nuevo_precio)
                else:
                    base = float(l.precio or 0.0)
                    l.precio = base * float(factor)
                count += 1

            session.flush()
            return count
