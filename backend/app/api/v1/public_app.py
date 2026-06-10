from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.rate_limiter import limiter
from slowapi.middleware import SlowAPIMiddleware
from app.api.v1.endpoints import public
from app.api.v1.endpoints.logs import public_router as logs_public_router
from app.api.v1.endpoints.training_data import public_router as training_data_public_router
from app.api.v1.endpoints.ai_feedback import public_router as ai_feedback_public_router
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
public_app.include_router(logs_public_router, prefix="/logs", tags=["Logs"])
public_app.include_router(training_data_public_router, prefix="/training-data", tags=["Training Data"])
public_app.include_router(ai_feedback_public_router, prefix="/ai-feedback", tags=["AI Feedback"])
