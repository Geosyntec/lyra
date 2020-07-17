from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles


import lyra
from lyra.api import api_router
from lyra.home import home_router
from lyra.core.config import settings


app = FastAPI(title="lyra", version=lyra.__version__)

app.include_router(api_router, prefix="/api")
app.include_router(home_router)

app.mount("/static", StaticFiles(directory="lyra/static"), name="static")
app.mount("/home/static", StaticFiles(directory="lyra/home/static"), name="home/static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_CORS_ORIGINS,
    allow_origin_regex=settings.ALLOW_CORS_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS", "POST"],
    allow_headers=["*"],
)
