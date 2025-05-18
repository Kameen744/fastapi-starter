from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import create_db_and_tables
from .router import api_router
from .crud.crud import create_initial_admin

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# app.include_router(api_router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_initial_admin()


@app.get("/")
def root():
    return {"message": "Welcome to FastAPI Auth Template"}
