import datetime
import os
import atexit

from sqlalchemy import create_engine, DateTime, Integer, String, func, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, mapped_column, Mapped

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB", "netology_flask")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5431")

PG_DSN = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(PG_DSN)
atexit.register(engine.dispose)
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):

    @property
    def id_dict(self):
        return {'id': self.id}

class User(Base):

    __tablename__ = "app_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(72), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    registration_time: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'registration_time': self.registration_time.isoformat()
        }

class Advertisement(Base):
    __tablename__ = "advertisements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    creation_time: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("app_users.id"), nullable=False)

    @property
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'creation_time': self.creation_time.isoformat(),
            'owner_id': self.owner_id
        }

Base.metadata.create_all(bind=engine)