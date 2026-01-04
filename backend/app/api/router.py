from fastapi import FastAPI
from app.api.router_detector import router as detector_router
"""
adding CORS middleware to the FastAPI app in order to allow the frontend application to communicate with the backend API without any cross-origin issues.
"""
from fastapi.middleware.cors import CORSMiddleware
from app.api import router_detector, router_consumption

origins = [
    "http://localhost:5173", # Puerto estándar de Vite
    "http://localhost:5174", # <--- AÑADE ESTE (El que estás usando ahora)
    "http://localhost:5175", # Añade este por si acaso en el futuro
    "http://localhost:3000", 
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
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

# --- ROUTER REGISTRATION ---
# Registramos el router maestro.
# Las rutas serán:
# - /api/v1/households
# - /api/v1/consumption/dashboard/{id}
app.include_router(router_consumption.router, prefix="/api/v1", tags=["Smart Water"])

@app.get("/")
def root():
    return {"message": "Welcome to the Smart Water API. Visit /docs for documentation."}
