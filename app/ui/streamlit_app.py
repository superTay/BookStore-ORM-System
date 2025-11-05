# app/ui/streamlit_app.py
import streamlit as st
from typing import List, Tuple

# --- Imports del backend ---
from config.database import Base, engine
from domain.models import libro as _libro
from domain.models import venta as _venta
from domain.models import usuario as _usuario
from domain.repositories.libros import RepositorioLibros
from domain.repositories.usuarios import RepositorioUsuarios
from domain.repositories.ventas import RepositorioVentas
from domain.services.facturacion import generar_factura
from domain.services.reports import generar_reporte

# --- Configuración inicial ---
st.set_page_config(
    page_title="📚 BookStore ORM System",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📦 BookStore ORM System — Admin Dashboard")

# --- Ensure tables exist ---
def ensure_tables():
    Base.metadata.create_all(bind=engine)

ensure_tables()

# --- Tabs principales ---
tabs = st.tabs(["📘 Books", "👤 Users", "💰 Sales", "🧾 Invoices", "📊 Reports"])

# ===============================================================
# 🟦 TAB 1: BOOKS
# ===============================================================
with tabs[0]:
    st.header("📘 Books Management")
    repo_books = RepositorioLibros()

    # --- Añadir nuevo libro ---
    with st.expander("➕ Add a new Book"):
        with st.form("add_book_form"):
            c1, c2 = st.columns(2)
            titulo = c1.text_input("Title")
            autor = c2.text_input("Author")

            c3, c4, c5 = st.columns(3)
            isbn = c3.text_input("ISBN (optional)")
            stock = c4.number_input("Stock", min_value=0, value=0, step=1)
            precio = c5.number_input("Price (€)", min_value=0.0, value=0.0, step=0.5, format="%.2f")

            submitted = st.form_submit_button("Add Book")
            if submitted:
                try:
                    repo_books.agregar_libro(titulo, autor, isbn or None, int(stock), float(precio))
                    st.success(f"✅ Book '{titulo}' added successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to add book: {e}")

    # --- Listado de libros ---
    st.subheader("📋 Book List")
    try:
        books = repo_books.listar_libros()
        if books:
            data = [
                {
                    "ID": b.id,
                    "Title": b.titulo,
                    "Author": b.autor,
                    "ISBN": b.isbn,
                    "Stock": b.stock,
                    "Price (€)": b.precio,
                }
                for b in books
            ]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No books found. Add a new one above.")
    except Exception as e:
        st.error(f"Error loading books: {e}")

    # --- Actualizar stock ---
    with st.expander("🔄 Update Stock"):
        if books:
            ids = [b.id for b in books]
            c1, c2 = st.columns(2)
            bid = c1.selectbox("Select Book ID", ids)
            new_stock = c2.number_input("New stock", min_value=0, step=1)
            if st.button("Update Stock"):
                updated = repo_books.actualizar_stock_libro(int(bid), int(new_stock))
                if updated:
                    st.success("✅ Stock updated successfully!")
                else:
                    st.warning("⚠️ Book not found.")

    # --- Eliminar libro ---
    with st.expander("🗑️ Delete Book"):
        if books:
            ids = [b.id for b in books]
            delete_id = st.selectbox("Select Book ID to delete", ids)
            if st.button("Delete Book"):
                try:
                    repo_books.eliminar_libro(int(delete_id))
                    st.success(f"Book with ID {delete_id} deleted successfully.")
                except Exception as e:
                    st.error(f"❌ Failed to delete book: {e}")

# ===============================================================
# 🟨 TAB 2: USERS
# ===============================================================
with tabs[1]:
    st.header("👤 User Management")
    repo_users = RepositorioUsuarios()

    with st.expander("➕ Add a new User"):
        with st.form("add_user_form"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Name")
            email = c2.text_input("Email")
            submitted = st.form_submit_button("Add User")
            if submitted:
                try:
                    repo_users.agregar_usuario(nombre, email)
                    st.success(f"✅ User '{nombre}' added successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to add user: {e}")

    st.subheader("📋 Users List")
    try:
        users = repo_users.listar_usuarios()
        if users:
            data = [{"ID": u.id, "Name": u.nombre, "Email": u.email} for u in users]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No users registered.")
    except Exception as e:
        st.error(f"Error loading users: {e}")

# ===============================================================
# 🟩 TAB 3: SALES
# ===============================================================
with tabs[2]:
    st.header("💰 Sales Management")
    repo_sales = RepositorioVentas()
    repo_books = RepositorioLibros()
    repo_users = RepositorioUsuarios()

    books = repo_books.listar_libros()
    users = repo_users.listar_usuarios()

    with st.expander("➕ Create a New Sale"):
        with st.form("create_sale_form"):
            c1, c2 = st.columns(2)
            cliente = c1.text_input("Customer Name")
            usuario_id = c2.selectbox(
                "Linked User (optional)",
                options=[None] + [u.id for u in users],
                format_func=lambda x: "None" if x is None else f"User {x}"
            )

            st.subheader("🛒 Items")
            item_count = st.number_input("Number of items", min_value=1, value=1, step=1)
            items: List[Tuple[int, int]] = []

            for i in range(int(item_count)):
                bcol, qcol = st.columns((3, 1))
                bid = bcol.selectbox(
                    f"Book #{i+1}",
                    options=[b.id for b in books] if books else [],
                    format_func=lambda x: next((b.titulo for b in books if b.id == x), str(x)),
                    key=f"book_{i}"
                )
                qty = qcol.number_input(f"Qty #{i+1}", min_value=1, value=1, step=1, key=f"qty_{i}")
                if bid:
                    items.append((int(bid), int(qty)))

            submitted = st.form_submit_button("Create Sale")
            if submitted:
                try:
                    venta = repo_sales.crear_venta(cliente or None, items, usuario_id=usuario_id)
                    st.success(f"✅ Sale created successfully (ID: {venta.id})")
                except Exception as e:
                    st.error(f"❌ Error creating sale: {e}")

    # --- Listado de ventas ---
    st.subheader("📋 Sales List")
    try:
        ventas = repo_sales.listar_ventas()
        if ventas:
            data = [
                {
                    "ID": v.id,
                    "Customer": v.cliente_nombre,
                    "Date": str(v.fecha_venta),
                    "Total (€)": v.total_venta,
                    "User ID": getattr(v, "usuario_id", None),
                }
                for v in ventas
            ]
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No sales recorded.")
    except Exception as e:
        st.error(f"Error loading sales: {e}")

# ===============================================================
# 🧾 TAB 4: INVOICES
# ===============================================================
with tabs[3]:
    st.header("🧾 Invoice Viewer")
    repo_sales = RepositorioVentas()
    ventas = repo_sales.listar_ventas()

    if ventas:
        vid = st.selectbox("Select Sale ID", [v.id for v in ventas], key="invoice_sale")
        if st.button("Show Invoice"):
            try:
                venta = repo_sales.obtener_venta_por_id(int(vid))
                if venta:
                    factura_texto = generar_factura(venta)
                    st.code(factura_texto, language="markdown")
            except Exception as e:
                st.error(f"❌ Error loading invoice: {e}")
    else:
        st.info("No sales available for invoices.")

# ===============================================================
# 📊 TAB 5: REPORTS
# ===============================================================
with tabs[4]:
    st.header("📊 Reports Generator")
    periodo = st.selectbox("Select Period", ["mensual", "trimestral", "anual"], index=0)
    nombre = st.text_input("Output file name", value=f"reporte_{periodo}.pdf")
    if st.button("Generate PDF Report"):
        try:
            generar_reporte(nombre, periodo)
            with open(nombre, "rb") as f:
                st.download_button("⬇️ Download Report", f, file_name=nombre)
            st.success(f"✅ Report generated successfully: {nombre}")
        except Exception as e:
            st.error(f"❌ Failed to generate report: {e}")

