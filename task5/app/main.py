from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.endpoints import doctors, patients, appointments

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    doctors.router,
    prefix=f"{settings.API_V1_STR}/doctors",
    tags=["doctors"]
)
app.include_router(
    patients.router,
    prefix=f"{settings.API_V1_STR}/patients",
    tags=["patients"]
)
app.include_router(
    appointments.router,
    prefix=f"{settings.API_V1_STR}/appointments",
    tags=["appointments"]
)


@app.get("/")
def root():
    """
    Root endpoint.
    
    Returns:
        dict: Welcome message
    """
    return {
        "message": "Welcome to the Doctor Appointment API",
        "version": settings.VERSION,
        "docs_url": "/docs"
    } 