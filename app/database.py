import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# DATABASE_URL comes from docker-compose
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL not install")

engine = create_engine(DATABASE_URL)

db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

from app.models import Base   # ← Safe to import now because models.py does not import database anymore

Base.query = db_session.query_property()

def init_db():
    from app import models  # Importing the models
    Base.metadata.create_all(bind=engine)
