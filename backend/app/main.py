from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import coach
import os

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "https://sample-firebase-ai-app-a0694.web.app",  # Firebase hosting
        "https://aicoach-g22l.onrender.com",  # Render deployment
        "https://accent-improver-backend-5636d63f4b47.herokuapp.com"  # Heroku deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(coach.router)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Accent Improver Backend"}
