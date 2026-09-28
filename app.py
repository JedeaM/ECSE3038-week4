# ECSE3038 - Week 4, Lecture 1 - starter
# Monday's API with the hard-coded list emptied.
# Run:  uvicorn app:app --reload

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError   # <-- import for handling duplicates

load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["ecse3038"]
devices = db["devices"]
devices.create_index("name", unique=True)   # <-- enforce unique names

app = FastAPI()


class Device(BaseModel):
    name: str
    room: str
    temp: float
    online: bool


readings = []


@app.get("/devices/{name}")
def get_device(name: str):
    device = devices.find_one({"name": name}, {"_id": 0})
    if device:
        return device
    raise HTTPException(status_code=404, detail="No device called " + name)


@app.get("/devices/{name}")
def get_device(name: str):
    for device in readings:
        if device["name"] == name:
            return device
    raise HTTPException(status_code=404, detail="No device called " + name)


@app.post("/devices", status_code=201)
def create_device(device: Device):
    new_device = device.model_dump()
    try:
        devices.insert_one(new_device)
    except DuplicateKeyError:
        
        raise HTTPException(status_code=409, detail="Device name already exists")
    new_device.pop("_id")
    return new_device
