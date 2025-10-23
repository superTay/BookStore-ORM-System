"""Persistence layer (Repository) for Libro CRUD operations.

Encapsulates database-session management and common operations over the
Libro model to keep application code decoupled from persistence details.
"""

from contextlib import contextmanager
from typing import Iterable, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database import SessionLocal
from libro import Libro


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
            return list(session.query(Libro).order_by(Libro.id.asc()).all())

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
