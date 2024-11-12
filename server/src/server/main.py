from fastapi import FastAPI

from .auth.routes import router as auth_router
from .middlewares import AuthenticationMiddleware
from .quizes.routes import router as quizes_router
from .users.routes import router as users_router

app = FastAPI()

app.include_router(quizes_router, prefix="/quizes", tags=["quizes"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])

app.add_middleware(AuthenticationMiddleware)
