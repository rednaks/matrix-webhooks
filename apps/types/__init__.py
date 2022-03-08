from typing import Optional

from pydantic import BaseModel


class MatrixConfig(BaseModel):
    homeserver: str
    user_id: str
    access_token: Optional[str]
    password: Optional[str]
