# ECSE3038 - Week 5, Lecture 1
# Readings Over Time
#
# Run:
# uvicorn app:app --reload

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone


# Load environment variables
load_dotenv()


# Connect to MongoDB
client = MongoClient(
    os.getenv("MONGODB_URI"),
    tz_aware=True
)

db = client["ecse3038"]

devices = db["devices"]
readings = db["readings"]


app = FastAPI()


# -------------------------
# Models
# -------------------------

class Device(BaseModel):
    mac: str
    name: str | None = None
    room: str | None = None


class Reading(BaseModel):
    mac: str
    temp: float


# -------------------------
# Database indexes
# -------------------------

devices.create_index(
    [("mac", ASCENDING)],
    unique=True
)


# -------------------------
# Devices
# -------------------------

@app.get("/devices/{mac}")
def get_device(mac: str):

    device = devices.find_one(
        {"mac": mac},
        {"_id": 0}
    )

    if device:
        return device

    raise HTTPException(
        status_code=404,
        detail="No device with MAC " + mac
    )


@app.post("/devices", status_code=201)
def create_device(device: Device):

    new_device = device.model_dump()

    try:
        devices.insert_one(new_device)

    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Device MAC already exists"
        )

    new_device.pop("_id", None)

    return new_device


# -------------------------
# Create a reading
# -------------------------

@app.post("/readings", status_code=201)
def create_reading(reading: Reading):

    # Make sure the device exists
    if devices.find_one({"mac": reading.mac}) is None:
        raise HTTPException(
            status_code=404,
            detail="No device with MAC " + reading.mac
        )

    # Convert the Pydantic model to a dictionary
    new_reading = reading.model_dump()

    # Server supplies the time
    new_reading["time"] = datetime.now(timezone.utc)

    # Store the reading
    readings.insert_one(new_reading)

    # Remove MongoDB's internal ID before returning
    new_reading.pop("_id", None)

    return new_reading


# -------------------------
# Get readings
# -------------------------

@app.get("/readings")
def get_readings(
    mac: str | None = None,
    since: datetime | None = None,
    limit: int = 10
):

    query = {}

    # Filter by MAC address if provided
    if mac is not None:
        query["mac"] = mac

    # Filter by time if provided
    if since is not None:
        query["time"] = {
            "$gte": since
        }

    # Get newest readings first
    result = readings.find(
        query,
        {"_id": 0}
    ).sort(
        "time",
        -1
    ).limit(limit)

    return list(result)


# -------------------------
# Get latest reading
# -------------------------

@app.get("/readings/latest")
def get_latest_reading(
    mac: str | None = None
):

    query = {}

    # If a MAC was supplied, only search that device
    if mac is not None:
        query["mac"] = mac

    reading = readings.find_one(
        query,
        {"_id": 0},
        sort=[("time", -1)]
    )

    if reading is None:
        raise HTTPException(
            status_code=404,
            detail="No readings yet"
        )

    return reading