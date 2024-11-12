from fastapi import FastAPI

from .auth.routes import router as auth_router
from .quizes.routes import router as quizes_router

app = FastAPI()
app.include_router(quizes_router, prefix="/quizes", tags=["quizes"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
