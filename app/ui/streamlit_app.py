import streamlit as st
from typing import List, Tuple

from config.database import Base, engine
from domain.models import libro as _libro  # ensure models are registered
from domain.models import venta as _venta  # ensure models are registered
from domain.models import usuario as _usuario  # ensure models are registered
from domain.repositories.libros import RepositorioLibros
from domain.repositories.usuarios import RepositorioUsuarios
from domain.repositories.ventas import RepositorioVentas
from domain.services.facturacion import generar_factura
from domain.services.reports import generar_reporte


def ensure_tables():
    Base.metadata.create_all(bind=engine)


st.set_page_config(page_title="BookStore ORM System", layout="wide")
st.title("BookStore ORM System — Admin UI (Local)")
ensure_tables()

tabs = st.tabs(["Books", "Users", "Sales", "Invoices", "Reports"]) 


with tabs[0]:
    st.header("Books")
    rl = RepositorioLibros()
    with st.form("add_book"):
        c1, c2 = st.columns(2)
        titulo = c1.text_input("Title", "")
        autor = c2.text_input("Author", "")
        c3, c4, c5 = st.columns(3)
        isbn = c3.text_input("ISBN", "")
        stock = c4.number_input("Stock", min_value=0, value=0, step=1)
        precio = c5.number_input("Price", min_value=0.0, value=0.0, step=0.5, format="%.2f")
        submitted = st.form_submit_button("Add Book")
        if submitted:
            try:
                rl.agregar_libro(titulo, autor, isbn or None, int(stock), float(precio))
                st.success("Book added")
            except Exception as e:
                st.error(f"Failed to add: {e}")

    st.subheader("List")
    books = rl.listar_libros()
    if books:
        # Convert to displayable rows
        data = [
            {
                "id": b.id,
                "titulo": b.titulo,
                "autor": b.autor,
                "isbn": b.isbn,
                "stock": b.stock,
                "precio": b.precio,
            }
            for b in books
        ]
        st.dataframe(data, use_container_width=True)

    st.subheader("Update stock")
    if books:
        ids = [b.id for b in books]
        bid = st.selectbox("Book ID", ids)
        new_stock = st.number_input("New stock", min_value=0, step=1)
        if st.button("Update"):
            updated = rl.actualizar_stock_libro(int(bid), int(new_stock))
            if updated:
                st.success("Stock updated")
            else:
                st.warning("Book not found")


with tabs[1]:
    st.header("Users")
    ru = RepositorioUsuarios()
    with st.form("add_user"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Name", "")
        email = c2.text_input("Email", "")
        submitted = st.form_submit_button("Add User")
        if submitted:
            try:
                ru.agregar_usuario(nombre, email)
                st.success("User added")
            except Exception as e:
                st.error(f"Failed to add: {e}")

    users = ru.listar_usuarios()
    if users:
        st.subheader("List")
        ud = [{"id": u.id, "nombre": u.nombre, "email": u.email} for u in users]
        st.dataframe(ud, use_container_width=True)


with tabs[2]:
    st.header("Sales")
    rv = RepositorioVentas()
    # Build item selectors
    rl = RepositorioLibros()
    books = rl.listar_libros()
    ru = RepositorioUsuarios()
    users = ru.listar_usuarios()

    with st.form("create_sale"):
        c0, c1 = st.columns(2)
        cliente = c0.text_input("Customer name", "")
        usuario_id = None
        if users:
            usuario_id = c1.selectbox(
                "User (optional)", options=[None] + [u.id for u in users], format_func=lambda x: "None" if x is None else f"{x}"
            )

        st.markdown("### Items")
        item_count = st.number_input("Number of items", min_value=1, value=1, step=1)
        items: List[Tuple[int, int]] = []
        for i in range(int(item_count)):
            bcol, qcol = st.columns((3, 1))
            bid = bcol.selectbox(
                f"Book #{i+1}", options=[b.id for b in books] if books else [], key=f"book_{i}"
            )
            qty = qcol.number_input(f"Qty #{i+1}", min_value=1, value=1, step=1, key=f"qty_{i}")
            if bid:
                items.append((int(bid), int(qty)))

        submitted = st.form_submit_button("Create Sale")
        if submitted:
            try:
                venta = rv.crear_venta(cliente or None, items, usuario_id=usuario_id)
                st.success(f"Sale created with id {venta.id}")
            except Exception as e:
                st.error(f"Failed to create sale: {e}")

    st.subheader("Sales list")
    ventas = rv.listar_ventas()
    if ventas:
        vd = [
            {
                "id": v.id,
                "cliente": v.cliente_nombre,
                "fecha": str(v.fecha_venta),
                "total": v.total_venta,
                "usuario_id": getattr(v, "usuario_id", None),
            }
            for v in ventas
        ]
        st.dataframe(vd, use_container_width=True)

    st.subheader("Update order items")
    if ventas and books:
        vid = st.selectbox("Sale ID", [v.id for v in ventas])
        new_count = st.number_input("New number of items", min_value=1, value=1, step=1)
        new_items: List[Tuple[int, int]] = []
        for i in range(int(new_count)):
            bcol, qcol = st.columns((3, 1))
            bid = bcol.selectbox(
                f"Book #{i+1} (new)", options=[b.id for b in books], key=f"nbook_{i}"
            )
            qty = qcol.number_input(f"Qty #{i+1} (new)", min_value=1, value=1, step=1, key=f"nqty_{i}")
            new_items.append((int(bid), int(qty)))
        if st.button("Update Sale"):
            try:
                rv.actualizar_pedido(int(vid), new_items)
                st.success("Sale updated")
            except Exception as e:
                st.error(f"Failed to update: {e}")


with tabs[3]:
    st.header("Invoices")
    rv = RepositorioVentas()
    ventas = rv.listar_ventas()
    if ventas:
        vid = st.selectbox("Sale ID", [v.id for v in ventas], key="invoice_sale")
        if st.button("Show Invoice"):
            v = rv.obtener_venta_por_id(int(vid))
            if v:
                st.text(generar_factura(v))


with tabs[4]:
    st.header("Reports")
    periodo = st.selectbox("Period", ["mensual", "trimestral", "anual"], index=0)
    nombre = st.text_input("Output file name", value=f"reporte_{periodo}.pdf")
    if st.button("Generate PDF report"):
        try:
            generar_reporte(nombre, periodo)  # type: ignore[arg-type]
            with open(nombre, "rb") as f:
                st.download_button("Download report", f, file_name=nombre)
            st.success(f"Report generated: {nombre}")
        except Exception as e:
            st.error(f"Failed to generate: {e}")

