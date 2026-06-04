from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload

app = FastAPI(
    title="NeuraCore API",
    description="Adaptive Learning for Neurodivergent Students",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "NeuraCore API is running 🧠"}
