from pathlib import Path
import secrets
from typing import Any, List, Optional, Union
from typing_extensions import Literal

from pydantic import AnyHttpUrl, BaseSettings, validator

import lyra


class Settings(BaseSettings):
    # API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    MNWD_FTP_USERNAME: str = ""
    MNWD_FTP_PASSWORD: str = ""
    MNWD_FTP_LOCATION: str = ""


    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FORCE_FOREGROUND: bool = False

    HYDSTRA_BASE_URL: str = ""

    # SERVER_NAME: str
    # SERVER_HOST: AnyHttpUrl

    # ALLOW_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    ALLOW_CORS_ORIGINS: List[Union[AnyHttpUrl, Literal["*"]]] = []
    ALLOW_CORS_ORIGIN_REGEX: Optional[str] = None

    @validator("ALLOW_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        env_prefix = "LYRA_"
        env_file = Path(lyra.__file__).absolute().parent.parent.parent.parent.parent / '.env'


settings = Settings()
