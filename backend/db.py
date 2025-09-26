# backend/db.py
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine("sqlite:///learnsync.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Section(Base):
    __tablename__ = "sections"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    resources = relationship("Resource", back_populates="section", cascade="all, delete-orphan")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(String, primary_key=True, index=True)
    section_id = Column(String, ForeignKey("sections.id"))
    url = Column(String)
    title = Column(String)
    description = Column(Text, nullable=True)
    thumbnail = Column(String, nullable=True)
    level = Column(String, nullable=True)   # user-specified or inferred
    similarity = Column(Float, nullable=True)
    suitable = Column(Boolean, nullable=True)
    embedding = Column(Text, nullable=True) # store embedding as stringified list

    section = relationship("Section", back_populates="resources")

def init_db():
    Base.metadata.create_all(bind=engine)
