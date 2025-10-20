from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
from .scheduler import scheduler

# ⬇️ import 子 App
from .api.v1.public_app import public_app
from .api.v1.internal_app import internal_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    scheduler.start()
    yield
    # Shut down the scheduler
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://192.168.1.133:5173"], # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 Public + Internal 子 App
app.mount(f"{settings.API_V1_STR}/public", public_app)
app.mount(f"{settings.API_V1_STR}", internal_app)

# 根目錄導向
@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")