from fastapi import FastAPI

from app.routes import user
from app.routes import trade


app = FastAPI(
    title="FC Online Trade API",
    version="0.1.0",
)


app.include_router(user.router)
app.include_router(trade.router)


@app.get("/")
async def root():
    return {
        "message": "FC Online Trade API"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }
