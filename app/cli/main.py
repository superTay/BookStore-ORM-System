"""Simple CLI/demo to create books and sales using repository layer.

Run examples:
    - python main.py seed-libros
    - python main.py crear-venta "Cliente Demo" 1:2 2:1

Commands
    seed-libros              Create a few sample books if table is empty.
    listar-libros            Print all books.
    crear-venta NAME ITEMS   Create a sale with items as pairs libro_id:cantidad.
    listar-ventas            Print all sales.
    actualizar-precios [--autor NAME] [--ids 1,2] [--min 0] [--max 100] [--precio 9.99 | --factor 1.1]
                             Bulk update book prices by filters.
    actualizar-pedido VENTA_ID ITEMS
                             Replace sale items (libro_id:cantidad ...) with stock reconciliation.
"""

import sys
from typing import List, Tuple

from config.database import Base, engine
from domain.models import libro  # ensure models are registered
from domain.models import venta  # ensure models are registered
from domain.repositories.libros import RepositorioLibros
from domain.repositories.ventas import RepositorioVentas


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


def cmd_actualizar_precios(args: List[str]):
    # naive arg parsing to avoid adding extra deps
    autor = None
    ids = None
    min_p = None
    max_p = None
    precio = None
    factor = None
    it = iter(args)
    for a in it:
        if a == "--autor":
            autor = next(it, None)
        elif a == "--ids":
            raw = next(it, "")
            ids = [int(x) for x in raw.split(",") if x]
        elif a == "--min":
            min_p = float(next(it, "0"))
        elif a == "--max":
            max_p = float(next(it, "0"))
        elif a == "--precio":
            precio = float(next(it, "0"))
        elif a == "--factor":
            factor = float(next(it, "0"))
        else:
            raise SystemExit(f"Unknown flag: {a}")
    repo = RepositorioLibros()
    changed = repo.actualizar_precios(
        autor=autor, ids=ids, min_precio=min_p, max_precio=max_p, nuevo_precio=precio, factor=factor
    )
    print(f"Updated {changed} book(s).")


def cmd_actualizar_pedido(venta_id_str: str, item_args: List[str]):
    venta_id = int(venta_id_str)
    items = parse_items(item_args)
    repo = RepositorioVentas()
    venta = repo.actualizar_pedido(venta_id, items)
    if not venta:
        print("Sale not found")
    else:
        print("Sale updated:", venta)


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
    elif cmd == "actualizar-precios":
        if len(sys.argv) < 3:
            raise SystemExit("Usage: python main.py actualizar-precios [--autor NAME] [--ids 1,2] [--min 0] [--max 100] [--precio 9.99 | --factor 1.1]")
        cmd_actualizar_precios(sys.argv[2:])
    elif cmd == "actualizar-pedido":
        if len(sys.argv) < 4:
            raise SystemExit("Usage: python main.py actualizar-pedido VENTA_ID libro_id:cantidad [libro_id:cantidad ...]")
        cmd_actualizar_pedido(sys.argv[2], sys.argv[3:])
    else:
        print("Unknown command.")
        print(__doc__)


if __name__ == "__main__":
    main()
