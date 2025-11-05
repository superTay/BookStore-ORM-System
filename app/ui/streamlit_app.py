# streamlit_app.py
# =====================================================
# Streamlit Admin Interface for BookStore ORM System
# Enhanced UI/UX version – professional single-file design
# =====================================================

import streamlit as st
from typing import List, Tuple
import pandas as pd

# --- ORM & Repositories ---
from config.database import Base, engine
from domain.models import libro as _libro
from domain.models import venta as _venta
from domain.models import usuario as _usuario
from domain.repositories.libros import RepositorioLibros
from domain.repositories.usuarios import RepositorioUsuarios
from domain.repositories.ventas import RepositorioVentas
from domain.services.facturacion import generar_factura
from domain.services.reports import generar_reporte


# -----------------------------------------------------
#  SETUP & PAGE CONFIGURATION
# -----------------------------------------------------
st.set_page_config(
    page_title="BookStore ORM System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📚 **BookStore ORM System — Admin Dashboard**")
st.caption("Manage your bookstore's catalog, users, sales, invoices, and reports.")


# -----------------------------------------------------
#  DATABASE INITIALIZATION
# -----------------------------------------------------
def ensure_tables():
    Base.metadata.create_all(bind=engine)


ensure_tables()


# -----------------------------------------------------
#  SESSION STATE INITIALIZATION
# -----------------------------------------------------
if "repos" not in st.session_state:
    st.session_state["repos"] = {
        "libros": RepositorioLibros(),
        "usuarios": RepositorioUsuarios(),
        "ventas": RepositorioVentas(),
    }

# Cache versioning for data refresh
if "data_version" not in st.session_state:
    st.session_state["data_version"] = 0


# -----------------------------------------------------
#  DATA CACHING UTILITIES
# -----------------------------------------------------

@st.cache_data(ttl=60)
def get_books(_repo):
    books = _repo.listar_libros()
    return pd.DataFrame(
        [
            {
                "ID": b.id,
                "Title": b.titulo,
                "Author": b.autor,
                "ISBN": b.isbn,
                "Stock": b.stock,
                "Price (€)": float(b.precio or 0.0),
            }
            for b in books
        ]
    )


@st.cache_data(ttl=60)
def get_users(_repo):
    users = _repo.listar_usuarios()
    return pd.DataFrame(
        [{"ID": u.id, "Name": u.nombre, "Email": u.email} for u in users]
    )


@st.cache_data(ttl=60)
def get_sales(_repo):
    ventas = _repo.listar_ventas()
    return pd.DataFrame(
        [
            {
                "ID": v.id,
                "Customer": v.cliente_nombre,
                "Date": str(v.fecha_venta),
                "Total (€)": float(v.total_venta or 0.0),
                "User ID": getattr(v, "usuario_id", None),
            }
            for v in ventas
        ]
    )


# -----------------------------------------------------
#  LAYOUT STRUCTURE — TABS
# -----------------------------------------------------
tabs = st.tabs(
    [
        "📚 Books",
        "👥 Users",
        "💰 Sales",
        "🧾 Invoices",
        "📈 Reports",
    ]
)


# =====================================================
#  TAB 1 — BOOKS
# =====================================================
with tabs[0]:
    st.header("📚 Books Management")
    repo = st.session_state["repos"]["libros"]

    with st.expander("➕ Add a New Book", expanded=False):
        with st.form("add_book"):
            c1, c2 = st.columns(2)
            titulo = c1.text_input("Title")
            autor = c2.text_input("Author")

            c3, c4, c5 = st.columns(3)
            isbn = c3.text_input("ISBN")
            stock = c4.number_input("Stock", min_value=0, value=0, step=1)
            precio = c5.number_input(
                "Price (€)", min_value=0.0, value=0.0, step=0.5, format="%.2f"
            )

            if st.form_submit_button("Add Book"):
                try:
                    repo.agregar_libro(titulo, autor, isbn or None, int(stock), float(precio))
                    st.success("✅ Book added successfully!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed to add book: {e}")

    st.subheader("📖 Book List")

    df_books = get_books(repo)
    if not df_books.empty:
        st.dataframe(df_books, use_container_width=True)
    else:
        st.info("No books found in database.")

    with st.expander("🔄 Update Stock"):
        if not df_books.empty:
            bid = st.selectbox("Book ID", df_books["ID"].tolist())
            new_stock = st.number_input("New Stock", min_value=0, step=1)
            if st.button("Update Stock"):
                try:
                    repo.actualizar_stock_libro(int(bid), int(new_stock))
                    st.success("✅ Stock updated successfully!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error updating stock: {e}")

    with st.expander("🗑️ Delete Book"):
        if not df_books.empty:
            del_id = st.selectbox("Select Book ID to Delete", df_books["ID"].tolist())
            if st.button("Delete Book"):
                try:
                    repo.eliminar_libro(int(del_id))
                    st.warning(f"Book {del_id} deleted.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error deleting book: {e}")


# =====================================================
#  TAB 2 — USERS
# =====================================================
with tabs[1]:
    st.header("👥 User Management")
    repo = st.session_state["repos"]["usuarios"]

    with st.expander("➕ Add a New User", expanded=False):
        with st.form("add_user"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Name")
            email = c2.text_input("Email")
            if st.form_submit_button("Add User"):
                try:
                    repo.agregar_usuario(nombre, email)
                    st.success("✅ User added successfully!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed to add user: {e}")

    st.subheader("👤 Registered Users")
    df_users = get_users(repo)
    if not df_users.empty:
        st.dataframe(df_users, use_container_width=True)
    else:
        st.info("No users registered yet.")


# =====================================================
#  TAB 3 — SALES
# =====================================================
with tabs[2]:
    st.header("💰 Sales Management")

    r_books = st.session_state["repos"]["libros"]
    r_users = st.session_state["repos"]["usuarios"]
    r_sales = st.session_state["repos"]["ventas"]

    df_books = get_books(r_books)
    df_users = get_users(r_users)

    with st.expander("➕ Create a New Sale", expanded=False):
        with st.form("create_sale"):
            c0, c1 = st.columns(2)
            cliente = c0.text_input("Customer Name")
            usuario_id = c1.selectbox(
                "Linked User (optional)",
                options=[None] + df_users["ID"].tolist() if not df_users.empty else [None],
            )

            st.markdown("#### Items")
            num_items = st.number_input("Number of Items", min_value=1, value=1, step=1)

            items: List[Tuple[int, int]] = []
            for i in range(int(num_items)):
                bcol, qcol = st.columns((3, 1))
                bid = bcol.selectbox(
                    f"Book #{i+1}",
                    options=df_books["ID"].tolist() if not df_books.empty else [],
                    format_func=lambda x: f"{x}",
                    key=f"book_{i}",
                )
                qty = qcol.number_input(
                    f"Qty #{i+1}", min_value=1, value=1, step=1, key=f"qty_{i}"
                )
                items.append((int(bid), int(qty)))

            if st.form_submit_button("Create Sale"):
                try:
                    venta = r_sales.crear_venta(cliente, items, usuario_id=usuario_id)
                    st.success(f"✅ Sale created successfully (ID: {venta.id})")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error creating sale: {e}")

    st.subheader("🧾 Sales List")
    df_sales = get_sales(r_sales)
    if not df_sales.empty:
        st.dataframe(df_sales, use_container_width=True)
    else:
        st.info("No sales yet.")


# =====================================================
#  TAB 4 — INVOICES
# =====================================================
with tabs[3]:
    st.header("🧾 Invoice Viewer")
    repo = st.session_state["repos"]["ventas"]
    ventas = repo.listar_ventas()
    if ventas:
        vid = st.selectbox("Select Sale ID", [v.id for v in ventas])
        if st.button("Show Invoice"):
            v = repo.obtener_venta_por_id(int(vid))
            if v:
                st.text(generar_factura(v))
    else:
        st.info("No invoices available yet.")


# =====================================================
#  TAB 5 — REPORTS
# =====================================================
with tabs[4]:
    st.header("📈 Reports & Analytics")

    r_sales = st.session_state["repos"]["ventas"]
    ventas = r_sales.listar_ventas()
    if ventas:
        periodo = st.selectbox("Report Period", ["Monthly", "Quarterly", "Annual"])
        nombre = st.text_input("Report Filename", f"report_{periodo.lower()}.pdf")

        if st.button("📄 Generate PDF Report"):
            try:
                generar_reporte(nombre, periodo.lower())
                with open(nombre, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Report",
                        data=f,
                        file_name=nombre,
                        mime="application/pdf",
                    )
                st.success(f"✅ Report '{nombre}' generated successfully!")
            except Exception as e:
                st.error(f"Failed to generate report: {e}")
    else:
        st.info("No sales available for report generation.")


