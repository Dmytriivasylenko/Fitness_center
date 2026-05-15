import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from app.models import Base


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

Base.query = db_session.query_property()

def init_db():
    from app import models  # Importing the models
    Base.metadata.create_all(bind=engine)
