from typing import Union
from fastapi.responses import JSONResponse


def success_handler(data: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "success",
            "code": "200_OK" if status_code == 200 else f"{status_code}_SUCCESS",
            "message": "Operation completed successfully",
            "data": data
        }
    )


def error_handler(error: Union[Exception, str], status_code: int = 500) -> JSONResponse:
    message = str(error) if isinstance(error, Exception) else error
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "code": f"{status_code}_ERROR",
            "message": message,
        }
    )