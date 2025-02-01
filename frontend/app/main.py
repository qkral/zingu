from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routers import coach
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS with more detailed logging
@app.middleware("http")
async def cors_logging_middleware(request: Request, call_next):
    # Log incoming request details
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = JSONResponse(content={"message": "Preflight request handled"})
        response.headers['Access-Control-Allow-Origin'] = "*"
        response.headers['Access-Control-Allow-Methods'] = "*"
        response.headers['Access-Control-Allow-Headers'] = "*"
        return response
    
    response = await call_next(request)
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "https://sample-firebase-ai-app-a0694.web.app",  # Firebase hosting
        "https://aicoach-g22l.onrender.com",  # Backend URL
        "*"  # Wildcard for debugging (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(coach.router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full exception details
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Request details: {request.method} {request.url}")
    logger.error(f"Full traceback:\n{traceback.format_exc()}")
    
    # Return a structured error response
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "details": traceback.format_exc()
        }
    )

@app.get("/")
async def root():
    return {"message": "Welcome to the Accent Improver API"}
