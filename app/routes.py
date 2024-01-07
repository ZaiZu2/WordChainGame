from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


@app.get("/")  # Use the decorator correctly here
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})
