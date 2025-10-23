from database import Base, engine, SessionLocal
from libro import Libro  # ensure model is imported so metadata includes it


def init_tables():
    Base.metadata.create_all(bind=engine)


def demo_insert():
    db = SessionLocal()
    try:
        # Create a demo book instance (prints on creation)
        book = Libro(
            titulo="El Quijote",
            autor="Miguel de Cervantes",
            isbn="9788491050291",
            stock=10,
            precio=19.99,
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        print("Inserted:", book)
    except Exception as e:
        db.rollback()
        print("Insert failed:", e)
    finally:
        db.close()


if __name__ == "__main__":
    init_tables()
    print("Tables created (if not existing).")
    # Uncomment to try a sample insert
    # demo_insert()

