"""Book domain model using SQLAlchemy ORM.

This module defines the `Libro` class, which maps to the `libros` table
in the MySQL database. It encapsulates the core attributes of a book and
provides a readable representation for debugging and logging.

Usage:
    - Import `Libro` from this module to work with book records.
    - Ensure the SQLAlchemy `Base` and `engine` are configured in
      `database.py` and that tables are created via `Base.metadata.create_all`.
"""

from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from config.database import Base


class Libro(Base):
    """SQLAlchemy ORM model for the `libros` table.

    Fields
    - id: Integer primary key with autoincrement.
    - titulo: Book title, required, up to 255 characters.
    - autor: Author name, required, up to 100 characters.
    - isbn: Optional 13-character ISBN, unique if provided.
    - stock: Optional available units in inventory.
    - precio: Optional unit price as floating point number.

    Notes
    - A uniqueness constraint is enforced for `isbn`.
    - The constructor prints a short message upon instance creation to help
      visualize object creation during demos or seeding.
    """

    __tablename__ = "libros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    autor = Column(String(100), nullable=False)
    isbn = Column(String(13), unique=True, nullable=True)
    stock = Column(Integer, nullable=True)
    precio = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("isbn", name="uq_libros_isbn"),
    )

    def __init__(self, titulo: str, autor: str, isbn: str | None = None, stock: int | None = None, precio: float | None = None):
        """Create a new in-memory Libro instance.

        Parameters
        - titulo: The book title (required).
        - autor: The book author (required).
        - isbn: Optional 13-character ISBN used as a unique identifier.
        - stock: Optional initial stock quantity.
        - precio: Optional unit price as a float.

        Side effects
        - Prints a short message confirming instance creation.
        """
        self.titulo = titulo
        self.autor = autor
        self.isbn = isbn
        self.stock = stock
        self.precio = precio
        print(f"Libro creado: '{self.titulo}' por {self.autor} (ISBN: {self.isbn or 'N/A'})")

    def __repr__(self) -> str:
        """Return a concise, developer-friendly textual representation.

        Example
            <Libro id=1 titulo='1984' autor='George Orwell' isbn='9780451524935' stock=5 precio=12.5>
        """
        return f"<Libro id={self.id} titulo={self.titulo!r} autor={self.autor!r} isbn={self.isbn!r} stock={self.stock} precio={self.precio}>"
