import importlib.resources as pkg_resources
import secrets
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import yaml
from pydantic import AnyHttpUrl, BaseSettings, validator

import lyra


class Settings(BaseSettings):
    # API_V1_STR: str = "/api/v1"
    VERSION: str = lyra.__version__
    ADMIN_USERNAME: str = ""
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    MNWD_FTP_USERNAME: str = ""
    MNWD_FTP_PASSWORD: str = ""
    MNWD_FTP_LOCATION: str = ""
    MNWD_FTP_DIRECTORY: str = ""

    AZURE_DATABASE_SERVER: str = ""
    AZURE_DATABASE_PORT: int = 9999
    AZURE_DATABASE_CONNECTION_TIMEOUT: int = 5
    AZURE_DATABASE_NAME: str = ""

    AZURE_DATABASE_USERNAME: str = ""
    AZURE_DATABASE_PASSWORD: str = ""
    AZURE_DATABASE_READONLY_USERNAME: str = ""
    AZURE_DATABASE_READONLY_PASSWORD: str = ""
    AZURE_DATABASE_WRITEONLY_USERNAME: str = ""
    AZURE_DATABASE_WRITEONLY_PASSWORD: str = ""

    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_STORAGE_SHARE_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_URL: str = ""

    @validator("AZURE_STORAGE_ACCOUNT_URL")
    def azure_account_url(cls, v: str, values: Dict[str, Any]) -> Any:
        if v:
            return v
        return (
            f"https://{values.get('AZURE_STORAGE_ACCOUNT_NAME')}.file.core.windows.net"
        )

    FORCE_FOREGROUND: bool = False
    FORCE_TASK_SCHEDULER_TO_FIVE_MINUTE_INTERVAL: bool = False
    ENABLE_BEAT_SCHEDULE: bool = False

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
        try:
            with pkg_resources.path("lyra", ".env") as p:
                env_file = p
        except FileNotFoundError:
            pass
        extra = "allow"

    def update(self, other: dict) -> None:
        for key, value in other.items():
            setattr(self, key, value)


settings = Settings()


def config():

    cfg_yml = pkg_resources.read_text("lyra.core", "lyra_config.yml")
    cfg = yaml.safe_load(cfg_yml)

    cfg["site_path"] = (
        Path(lyra.__file__).parent / "data/mount/swn/hydstra"
    ).resolve() / "swn_sites.json"

    return cfg


cfg = config()
