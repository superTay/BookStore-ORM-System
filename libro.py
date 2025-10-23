from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from database import Base


class Libro(Base):
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
        self.titulo = titulo
        self.autor = autor
        self.isbn = isbn
        self.stock = stock
        self.precio = precio
        print(f"Libro creado: '{self.titulo}' por {self.autor} (ISBN: {self.isbn or 'N/A'})")

    def __repr__(self) -> str:
        return f"<Libro id={self.id} titulo={self.titulo!r} autor={self.autor!r} isbn={self.isbn!r} stock={self.stock} precio={self.precio}>"


