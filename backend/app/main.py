from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import coach, translation
import os
import logging

app = FastAPI()

# Configure logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d - %(funcName)s'
)

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
app.include_router(coach.router, prefix="/api/coach")
app.include_router(translation.router)

@app.on_event("startup")
async def startup_event():
    print("\n--- Registered Routes ---")
    for route in app.routes:
        print(f"Path: {route.path}, Methods: {route.methods}, Name: {route.name}")
    print("--- End of Routes ---\n")
    
    # Additional debugging for translation router
    print("\n--- Translation Router Routes ---")
    for route in translation.router.routes:
        print(f"Path: {route.path}, Methods: {route.methods}, Name: {route.name}")
    print("--- End of Translation Router Routes ---\n")

# Root endpoint
@app.get("/")
def root():
    return {"message": "Accent Improver Backend"}
