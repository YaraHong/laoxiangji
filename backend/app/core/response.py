from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """标准返回结构"""
    code: int = 0
    message: str = "success"
    data: T | None = None


class PageData(BaseModel, Generic[T]):
    """分页数据结构"""
    items: list[T]
    total: int


def success(data: Any = None, message: str = "success") -> JSONResponse:
    """成功响应"""
    return JSONResponse(content=jsonable_encoder({
        "code": 0,
        "message": message,
        "data": data,
    }))


def error(code: int = 1, message: str = "error", status_code: int = 400) -> JSONResponse:
    """错误响应"""
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({
            "code": code,
            "message": message,
            "data": None,
        }),
    )


def page(items: list[Any], total: int) -> JSONResponse:
    """分页列表响应"""
    return success({"items": items, "total": total})
