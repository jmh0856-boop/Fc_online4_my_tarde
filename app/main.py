from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.routes import trade
from app.routes import user


app = FastAPI(
    title="FC Online Trade API",
    version="0.1.0",
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


templates = Jinja2Templates(
    directory="app/templates",
)


app.include_router(user.router)
app.include_router(trade.router)


class ApiKeyRequest(BaseModel):
    api_key: str


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.post("/api-key")
async def set_api_key(data: ApiKeyRequest):

    api_key = data.api_key.strip()

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="API Key를 입력해주세요.",
        )

    return {
        "success": True,
        "message": "API Key가 입력되었습니다.",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }