from sqlalchemy import Column, Integer, String
from app.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, unique=True, index=True)
    model = Column(String)
    current_version = Column(String)
    status = Column(String)
