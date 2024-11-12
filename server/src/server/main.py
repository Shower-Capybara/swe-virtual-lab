from fastapi import FastAPI

from .middlewares import AuthenticationMiddleware
from .routes.auth.routes import router as auth_router
from .routes.quizes.routes import router as quizes_router
from .routes.users.routes import router as users_router

app = FastAPI()

app.include_router(quizes_router, prefix="/quizes", tags=["quizes"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])

app.add_middleware(AuthenticationMiddleware)
