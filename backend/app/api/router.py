from fastapi import FastAPI
from app.api.router_detector import router as detector_router
"""
adding CORS middleware to the FastAPI app in order to allow the frontend application to communicate with the backend API without any cross-origin issues.
"""
from fastapi.middleware.cors import CORSMiddleware
from app.api import router_detector

origins = [
    "http://localhost:5173",
    "http://localhost:3000",  # React default port
]

app = FastAPI(
    title="Water Leak Detection API",
    description="API for detecting water leaks in household consumption data using LSTM Autoencoder.",
    version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_detector.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to the Water Leak Detection API. Visit /docs for API documentation."}

