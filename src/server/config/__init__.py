import os
from typing import Annotated, cast

from pydantic import Discriminator, TypeAdapter

from .local import TestSettings
from .real import RealSettings

Settings = Annotated[TestSettings | RealSettings, Discriminator("ENV")]

try:
    settings = cast(
        Settings,
        TypeAdapter(Settings).validate_python({"ENV": os.getenv("ENV", "real")}),
    )  # type: ignore[call-arg]
except Exception as e:
    print(f"Failed to init settings: {e!r}")
