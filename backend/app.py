import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from fastapi import FastAPI
from backend.routes.api import router

app = FastAPI(title="Intelligent Talent Acquisition Assistant")

# Include API routes
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Intelligent Talent Acquisition Assistant API"}
