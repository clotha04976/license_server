from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, customers, products, features, admin
from app.core.rate_limiter import limiter
from slowapi.middleware import SlowAPIMiddleware

internal_app = FastAPI()

# 加入速率限制 middleware
internal_app.state.limiter = limiter
internal_app.add_middleware(SlowAPIMiddleware)

# 僅允許特定來源（如內網前端）
internal_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://192.168.1.133:5173",
        "https://ducky.shinping.synology.me"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 限制允許的 HTTP 方法
    allow_headers=["Authorization", "Content-Type"],  # 限制允許的標頭
)

internal_app.include_router(auth.router, prefix="/auth", tags=["Auth"])
internal_app.include_router(customers.router, prefix="/customers", tags=["Customers"])
internal_app.include_router(products.router, prefix="/products", tags=["Products"])
internal_app.include_router(features.router, prefix="/features", tags=["Features"])
internal_app.include_router(admin.router, prefix="/admin", tags=["Admin"])  # 👉 加上 /admin
