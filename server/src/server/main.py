from fastapi import FastAPI

from .quizes.routes import router

app = FastAPI()
app.include_router(router, prefix="/quizes")
