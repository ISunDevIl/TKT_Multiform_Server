from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import SQLModel
from app.database import engine
from app.routers import public
# from app.routers import admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(title="TKT Multiform Server", lifespan=lifespan)

app.include_router(public.router)

@app.get("/")
def root():
    return {"message": "Service is running on multiform.tkt.ai.vn"}