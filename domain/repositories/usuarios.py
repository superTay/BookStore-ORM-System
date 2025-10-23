"""Repository layer for Usuario CRUD operations.

Provides a focused API for creating, listing, retrieving and deleting
Usuario entities, encapsulating session management and transactions.
"""

from typing import Iterable, Optional

from sqlalchemy.exc import SQLAlchemyError

from config.database import SessionLocal
from domain.models.usuario import Usuario


class RepositorioUsuarios:
    def _session(self):
        return SessionLocal()

    def agregar_usuario(self, nombre: str, email: str) -> Usuario:
        session = self._session()
        try:
            u = Usuario(nombre=nombre, email=email)
            session.add(u)
            session.commit()
            session.refresh(u)
            return u
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def listar_usuarios(self) -> Iterable[Usuario]:
        with self._session() as session:
            return list(session.query(Usuario).order_by(Usuario.id.asc()).all())

    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[Usuario]:
        with self._session() as session:
            return session.get(Usuario, usuario_id)

    def eliminar_usuario(self, usuario_id: int) -> bool:
        session = self._session()
        try:
            u = session.get(Usuario, usuario_id)
            if not u:
                return False
            session.delete(u)
            session.commit()
            return True
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()
