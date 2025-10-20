from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.rate_limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from app.api.v1.endpoints import public
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request


public_app = FastAPI()

# ➕ 加入限流 middleware（只作用於 public_app）
public_app.state.limiter = limiter
public_app.add_middleware(SlowAPIMiddleware)

# CORS 設定
public_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加入路由
public_app.include_router(public.router)
