from fastapi import HTTPException, status


class UnauthorizedException(HTTPException):
    """Exception raised for unauthorized access."""

    status_code = status.HTTP_401_UNAUTHORIZED
    headers = {"WWW-Authenticate": "Bearer"}

    def __init__(self, detail: str = "Unauthorized access"):
        self.detail = detail
