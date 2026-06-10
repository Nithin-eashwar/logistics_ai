from sqlalchemy import create_engine, Column, Integer, String, Float, JSON
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./logistics.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class DBOrder(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    priority = Column(Integer, nullable=False)
    destination = Column(String, nullable=True)

class DBOptimizationRun(Base):
    __tablename__ = "optimization_runs"
    id = Column(Integer, primary_key=True, index=True)
    total_orders = Column(Integer, nullable=False)
    total_distance = Column(Float, nullable=False)
    elapsed_ms = Column(Float, nullable=False)
    # Storing the vans output as JSON for simplicity
    vans_data = Column(JSON, nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
