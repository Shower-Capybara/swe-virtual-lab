from typing import Any

from sqlalchemy import JSON, ColumnElement, Function, func, sql
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql.type_api import TypeEngine


def json_build_object(values: dict[Any, Any]) -> Function[Any]:
    args = tuple(x for item in values.items() for x in item)
    return func.json_build_object(*args)


def empty_array(tp: type[TypeEngine] = JSON) -> ColumnElement:
    return sql.cast(sql.literal("{}"), ARRAY(tp))
