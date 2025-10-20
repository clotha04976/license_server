from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, customers, products, features, admin

internal_app = FastAPI()

# 僅允許特定來源（如內網前端）
internal_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://192.168.1.133:5173",
        "https://ducky.shinping.synology.me"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

internal_app.include_router(auth.router, prefix="/auth", tags=["Auth"])
internal_app.include_router(customers.router, prefix="/customers", tags=["Customers"])
internal_app.include_router(products.router, prefix="/products", tags=["Products"])
internal_app.include_router(features.router, prefix="/features", tags=["Features"])
internal_app.include_router(admin.router, prefix="/admin", tags=["Admin"])  # 👉 加上 /admin
