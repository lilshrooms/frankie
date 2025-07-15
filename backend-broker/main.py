from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import yaml

CRITERIA_DIR = os.path.join(os.path.dirname(__file__), '../criteria')

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/criteria", response_model=List[str])
def list_criteria():
    files = [f for f in os.listdir(CRITERIA_DIR) if f.endswith('.yaml')]
    return files

@app.get("/criteria/{loan_type}")
def get_criteria(loan_type: str):
    path = os.path.join(CRITERIA_DIR, f"{loan_type}.yaml")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Criteria not found")
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return data
