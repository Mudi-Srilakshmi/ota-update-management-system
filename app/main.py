from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, Base, get_db
from app.models.vehicle import Vehicle
from app.models.update import OTAUpdate
from app.models.schemas import (
    VehicleCreate,
    VehicleOut,
    OTAUpdateCreate,
    OTAUpdateOut
)

app = FastAPI(title="OTA Update Management System")

# ---------------- AUTHENTICATION ----------------
API_TOKEN = "SECRET_OTA_TOKEN"

def verify_token(x_api_token: str = Header(...)):
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------- DATABASE ----------------
Base.metadata.create_all(bind=engine)


# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {"message": "OTA Backend is running"}


# ---------------- VEHICLES ----------------
@app.post("/vehicles")
def add_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    new_vehicle = Vehicle(
        vehicle_id=vehicle.vehicle_id,
        model=vehicle.model,
        current_version=vehicle.current_version,
        status=vehicle.status
    )
    db.add(new_vehicle)
    db.commit()
    return {"message": "Vehicle added"}


@app.get("/vehicles", response_model=List[VehicleOut])
def get_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).all()


# ---------------- OTA UPDATES ----------------

# Assign OTA update (with strong validations)
@app.post(
    "/updates",
    response_model=OTAUpdateOut,
    dependencies=[Depends(verify_token)]
)
def assign_update(update: OTAUpdateCreate, db: Session = Depends(get_db)):

    # Prevent duplicate active OTA
    existing_ota = db.query(OTAUpdate).filter(
        OTAUpdate.vehicle_id == update.vehicle_id,
        OTAUpdate.status.in_(["PENDING", "IN_PROGRESS"])
    ).first()

    if existing_ota:
        raise HTTPException(
            status_code=400,
            detail="An OTA update is already active for this vehicle"
        )

    # Fetch vehicle
    vehicle = db.query(Vehicle).filter(
        Vehicle.vehicle_id == update.vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    #  Version mismatch validation
    if vehicle.current_version != update.from_version:
        raise HTTPException(
            status_code=400,
            detail=f"Version mismatch: vehicle is on {vehicle.current_version}"
        )

    # Create OTA update
    ota = OTAUpdate(
        vehicle_id=update.vehicle_id,
        from_version=update.from_version,
        to_version=update.to_version,
        status="PENDING"
    )

    db.add(ota)
    db.commit()
    db.refresh(ota)
    return ota


# Start OTA update
@app.post(
    "/updates/{update_id}/start",
    response_model=OTAUpdateOut,
    dependencies=[Depends(verify_token)]
)
def start_ota_update(update_id: int, db: Session = Depends(get_db)):
    ota = db.query(OTAUpdate).filter(OTAUpdate.id == update_id).first()

    if not ota:
        raise HTTPException(status_code=404, detail="OTA update not found")

    if ota.status != "PENDING":
        raise HTTPException(status_code=400, detail="OTA update cannot be started")

    ota.status = "IN_PROGRESS"
    db.commit()
    db.refresh(ota)
    return ota


# Complete OTA update
@app.post(
    "/updates/{update_id}/complete",
    response_model=OTAUpdateOut,
    dependencies=[Depends(verify_token)]
)
def complete_ota_update(update_id: int, db: Session = Depends(get_db)):
    ota = db.query(OTAUpdate).filter(OTAUpdate.id == update_id).first()

    if not ota:
        raise HTTPException(status_code=404, detail="OTA update not found")

    if ota.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="OTA update is not in progress"
        )

    vehicle = db.query(Vehicle).filter(
        Vehicle.vehicle_id == ota.vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Update vehicle version
    vehicle.current_version = ota.to_version

    # Mark OTA completed
    ota.status = "COMPLETED"

    db.commit()
    db.refresh(ota)
    return ota


# Fail OTA update
@app.post(
    "/updates/{update_id}/fail",
    response_model=OTAUpdateOut,
    dependencies=[Depends(verify_token)]
)
def fail_ota_update(update_id: int, db: Session = Depends(get_db)):
    ota = db.query(OTAUpdate).filter(OTAUpdate.id == update_id).first()

    if not ota:
        raise HTTPException(status_code=404, detail="OTA update not found")

    if ota.status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="Only IN_PROGRESS updates can be failed"
        )

    ota.status = "FAILED"
    db.commit()
    db.refresh(ota)
    return ota


# ---------------- OTA HISTORY ----------------
@app.get(
    "/vehicles/{vehicle_id}/updates",
    response_model=List[OTAUpdateOut]
)
def get_ota_history(vehicle_id: str, db: Session = Depends(get_db)):

    vehicle = db.query(Vehicle).filter(
        Vehicle.vehicle_id == vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    updates = db.query(OTAUpdate).filter(
        OTAUpdate.vehicle_id == vehicle_id
    ).order_by(OTAUpdate.id.desc()).all()

    return updates
