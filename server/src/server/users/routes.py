from fastapi import APIRouter

from server.authentication.utils import protected_route

router = APIRouter()


@router.get("/me")
@protected_route
async def get_me():
    pass
