from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class OTAUpdate(Base):
    __tablename__ = "ota_updates"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"))
    from_version = Column(String)
    to_version = Column(String)
    status = Column(String) 
