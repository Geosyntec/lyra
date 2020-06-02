from fastapi import FastAPI

from lyra.api import api_router


app = FastAPI(title="lyra")

app.include_router(api_router)
