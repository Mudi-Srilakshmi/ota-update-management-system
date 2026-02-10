from pydantic import BaseModel

class VehicleCreate(BaseModel):
    vehicle_id: str
    model: str
    current_version: str
    status: str


class VehicleOut(BaseModel):
    id: int
    vehicle_id: str
    model: str
    current_version: str
    status: str

    class Config:
        from_attributes = True


class OTAUpdateCreate(BaseModel):
    vehicle_id: str
    from_version: str
    to_version: str


class OTAUpdateOut(BaseModel):
    id: int
    vehicle_id: str
    from_version: str
    to_version: str
    status: str

    class Config:
        from_attributes = True
