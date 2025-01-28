from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# DATABASE_URL = "postgresql+psycopg2://user:password@192.168.50.40:20000/symon-agent"
DATABASE_URL = "sqlite:///database/sqlite.db?check_same_thread=False"

engine = create_engine(
    DATABASE_URL
)  # TODO: postgresql: , pool_recycle=3600, connect_args={"server_settings": {"jit": "off"}}
Session = sessionmaker(bind=engine)
Base = declarative_base()


def get_session() -> Session:
    db = Session()
    try:
        yield db
    finally:
        db.close()
