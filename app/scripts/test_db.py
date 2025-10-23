from sqlalchemy import text
from config.database import engine

def main():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
        print(f"Connection OK. SELECT 1 -> {result}")
    except Exception as e:
        print("Connection FAILED:", e)

if __name__ == "__main__":
    main()
