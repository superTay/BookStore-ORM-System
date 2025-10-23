"""Simple CLI/demo to create books and sales using repository layer.

Run examples:
    - python main.py seed-libros
    - python main.py crear-venta "Cliente Demo" 1:2 2:1

Commands
    seed-libros              Create a few sample books if table is empty.
    listar-libros            Print all books.
    crear-venta NAME ITEMS   Create a sale with items as pairs libro_id:cantidad.
    listar-ventas            Print all sales.
"""

import sys
from typing import List, Tuple

from database import Base, engine
import libro  # ensure models are registered
import venta  # ensure models are registered
from repositorio import RepositorioLibros
from repositorio_ventas import RepositorioVentas


def ensure_tables():
    Base.metadata.create_all(bind=engine)


def parse_items(args: List[str]) -> List[Tuple[int, int]]:
    items: List[Tuple[int, int]] = []
    for a in args:
        try:
            lid, qty = a.split(":", 1)
            items.append((int(lid), int(qty)))
        except Exception:
            raise SystemExit(f"Invalid item format '{a}'. Use libro_id:cantidad, e.g., 1:2")
    return items


def cmd_seed_libros():
    repo = RepositorioLibros()
    existentes = repo.listar_libros()
    if existentes:
        print("Books already exist; skipping seed.")
        return
    datos = [
        ("1984", "George Orwell", "9780451524935", 5, 12.5),
        ("El Quijote", "Miguel de Cervantes", "9788491050291", 10, 19.99),
        ("Cien años de soledad", "Gabriel García Márquez", "9780307474728", 7, 14.99),
    ]
    for t, a, i, s, p in datos:
        try:
            repo.agregar_libro(t, a, i, s, p)
        except Exception as e:
            print("Seed insert failed:", e)
    print("Seed complete.")


def cmd_listar_libros():
    repo = RepositorioLibros()
    for l in repo.listar_libros():
        print(l)


def cmd_crear_venta(nombre: str, item_args: List[str]):
    items = parse_items(item_args)
    repo = RepositorioVentas()
    venta = repo.crear_venta(nombre, items)
    print("Venta creada:", venta)


def cmd_listar_ventas():
    repo = RepositorioVentas()
    for v in repo.listar_ventas():
        print(v)


def main():
    ensure_tables()
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "seed-libros":
        cmd_seed_libros()
    elif cmd == "listar-libros":
        cmd_listar_libros()
    elif cmd == "crear-venta":
        if len(sys.argv) < 4:
            raise SystemExit("Usage: python main.py crear-venta NOMBRE libro_id:cantidad [libro_id:cantidad ...]")
        nombre = sys.argv[2]
        cmd_crear_venta(nombre, sys.argv[3:])
    elif cmd == "listar-ventas":
        cmd_listar_ventas()
    else:
        print("Unknown command.")
        print(__doc__)


if __name__ == "__main__":
    main()

