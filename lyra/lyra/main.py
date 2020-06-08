from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from lyra.api import api_router
from lyra.home import home_router


app = FastAPI(title="lyra")

app.include_router(api_router, prefix="/api")
app.include_router(home_router)

app.mount("/static", StaticFiles(directory="lyra/static"), name="static")
app.mount("/home/static", StaticFiles(directory="lyra/home/static"), name="home/static")
