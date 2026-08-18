from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import trade
from app.routes import user


app = FastAPI(
    title="FC Online Trade API",
    version="0.1.0",
)


# 정적 파일
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


# 템플릿
templates = Jinja2Templates(
    directory="app/templates",
)


# API 라우터
app.include_router(user.router)
app.include_router(trade.router)


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }