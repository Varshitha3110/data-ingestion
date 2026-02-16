from sqlalchemy import create_engine, text
import logging

logger = logging.getLogger("backend-2.db")

engine = create_engine(
    "sqlite:///./demo.db",
    echo=False,
    connect_args={"check_same_thread": False}
)

def init_db():
    logger.info("Initializing database")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

def save_name(name: str):
    logger.info("Saving name to database: %s", name)
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO requests (name) VALUES (:name)"),
            {"name": name}
        )
        conn.commit()
    logger.info("Database insert completed")
