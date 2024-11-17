from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .middlewares import AuthenticationMiddleware
from .routes.auth.routes import router as auth_router
from .routes.platform_stats.routes import router as platform_stats_router
from .routes.quizes.routes import router as quizes_router
from .routes.users.routes import router as users_router

app = FastAPI()

app.include_router(quizes_router, prefix="/quizes", tags=["quizes"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(
    platform_stats_router,
    prefix="/platform_stats",
    tags=["platform_stats"],
)

app.add_middleware(AuthenticationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
