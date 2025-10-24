BookStore ORM System
====================

Overview
This project is a simple, extensible bookstore backend implemented with Python, SQLAlchemy (ORM), and MySQL. It demonstrates clean layering with explicit configuration, domain models, repository-based persistence, and a lightweight CLI for common operations.

Key Features
- Secure configuration via .env (no passwords in code)
- SQLAlchemy models for Libro, Venta/DetalleVenta, and Usuario
- Repository layer encapsulating transactions and session management
- CLI commands to seed, list, create sales, and update entities
- Ready to evolve with migrations (Alembic) and tests

Project Structure
- config/
  - database.py — Loads .env, builds DATABASE_URL, provides `engine`, `Base`, and `SessionLocal`.
- domain/
  - models/
    - libro.py — Book model (libros): id, titulo, autor, isbn (unique), stock, precio.
    - venta.py — Sales models: `Venta` (header) and `DetalleVenta` (line items). `Venta` has many `DetalleVenta`.
    - usuario.py — User model (usuarios), one-to-many with `Venta` via `usuario_id` in ventas.
  - repositories/
    - libros.py — `RepositorioLibros`: CRUD for `Libro` plus bulk price updates.
    - ventas.py — `RepositorioVentas`: create sale (with stock validation and auto-decrement), update order atomically, list/get/delete.
    - usuarios.py — `RepositorioUsuarios`: create/list/get/delete users.
- app/
  - cli/
    - main.py — Simple CLI to seed data, create sales, list entities, and run updates.
  - scripts/
    - init_db.py — Create tables for registered models.
    - test_db.py — Smoke test for DB connectivity (SELECT 1).
- .env, .env.example — Environment configuration (ignored by Git).
- requirements.txt — Minimal runtime dependencies.

Configuration
Create a .env file (use .env.example as a template):
- DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
The `config/database.py` module loads these variables and constructs a SQLAlchemy URL for MySQL with PyMySQL.

Domain Models
- Libro (domain/models/libro.py)
  - Columns: id (PK), titulo (str, required), autor (str, required), isbn (str, unique), stock (int), precio (float)
  - Prints a short message on instance creation (useful for demos/seeding)
  - __repr__ provides a concise developer-friendly representation
- Venta and DetalleVenta (domain/models/venta.py)
  - Venta: id (PK), usuario_id (FK to usuarios), cliente_nombre, fecha_venta (UTC now), total_venta (float)
  - DetalleVenta: id (PK), venta_id (FK to ventas, cascade delete), libro_id (FK to libros, restrict), cantidad (int)
  - Relationships: Venta.detalles, DetalleVenta.venta, DetalleVenta.libro
- Usuario (domain/models/usuario.py)
  - Columns: id (PK), nombre, email
  - Relationship: Usuario.ventas (one-to-many to Venta), Venta.usuario (back-populated)

Persistence Layer (Repositories)
Repositories encapsulate session lifecycle, transactions (commit/rollback), and DB exceptions. Application code interacts with repositories instead of raw sessions.

- RepositorioLibros (domain/repositories/libros.py)
  - agregar_libro(titulo, autor, isbn=None, stock=None, precio=None) -> Libro
  - listar_libros() -> list[Libro]
  - actualizar_stock_libro(libro_id, nuevo_stock) -> Optional[Libro]
  - obtener_libro_por_id(libro_id) -> Optional[Libro]
  - eliminar_libro(libro_id) -> bool
  - actualizar_precios(autor=None, ids=None, min_precio=None, max_precio=None, nuevo_precio=None, factor=None) -> int
- RepositorioVentas (domain/repositories/ventas.py)
  - crear_venta(cliente_nombre, items, usuario_id=None) -> Venta
    - items: sequence of (libro_id, cantidad)
    - Validates stock, decrements stock atomically, computes total_venta
  - actualizar_pedido(venta_id, items) -> Optional[Venta]
    - Restores stock from current lines, validates new items, decrements stock, recomputes total
  - obtener_venta_por_id(venta_id) -> Optional[Venta]
  - listar_ventas() -> list[Venta]
  - eliminar_venta(venta_id) -> bool
- RepositorioUsuarios (domain/repositories/usuarios.py)
  - agregar_usuario(nombre, email) -> Usuario
  - listar_usuarios() -> list[Usuario]
  - obtener_usuario_por_id(usuario_id) -> Optional[Usuario]
  - eliminar_usuario(usuario_id) -> bool

CLI Usage
Ensure dependencies are installed and .env is set, then:
- Preferred (via project runner):
  - Create tables: `python manage.py init-db`
  - Check DB connectivity: `python manage.py test-db`
  - Seed example books: `python manage.py cli seed-libros`
  - List books: `python manage.py cli listar-libros`
  - Create a sale: `python manage.py cli crear-venta "Cliente Demo" 1:2 2:1`
  - List sales: `python manage.py cli listar-ventas`
  - Bulk update prices:
    - `python manage.py cli actualizar-precios --autor "George Orwell" --factor 1.1`
    - `python manage.py cli actualizar-precios --ids 1,2 --precio 9.99`
  - Update an order (replace items):
    - `python manage.py cli actualizar-pedido 1 1:3 2:1`

Direct module execution (alternative):
- Create tables: `python -m app.scripts.init_db`
- Check DB connectivity: `python -m app.scripts.test_db`
- Run CLI: `python -m app.cli.main listar-libros`

Development Notes
- Keep secrets in .env; .env is ignored by Git.
- Repositories own transactions; avoid calling session.commit() in CLI or service code.
- When adding new models, import them before calling `Base.metadata.create_all` so they are registered.
- Consider adding Alembic for versioned schema migrations as the schema evolves.

Requirements
- Python 3.11+
- MySQL server accessible via the configured host/port
- Packages: SQLAlchemy, PyMySQL, python-dotenv (see requirements.txt)

Local UI (Streamlit)
- Install Streamlit in your environment:
  - `python -m pip install streamlit`
- Run the local admin UI:
  - `streamlit run app/ui/streamlit_app.py`
- Features available:
  - Books: create, list, update stock
  - Users: create, list
  - Sales: create sale with optional user link, list, update items
  - Invoices: view generated invoice text per sale
  - Reports: generate and download PDF billing reports (monthly/quarterly/annual)

License
This repository is provided without a license header. Add your preferred license if you plan to distribute it.
