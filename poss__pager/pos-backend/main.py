import uvicorn
import os
from dotenv import load_dotenv

# 1. Load local .env (Docker will ignore this and use its own shell variables)
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, products, orders, settings_router, staff, ingredients, recipes, dashboard
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="POS Backend - FastAPI")

# 2. SMART CORS LOGIC
# Priority: Docker Env Variable > .env File > Localhost Default
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 3. REGISTER ROUTERS
app.include_router(auth.router, prefix="/auth")
app.include_router(products.router, prefix="/products")
app.include_router(orders.router, prefix="/orders")
app.include_router(settings_router.router, prefix="/settings")
app.include_router(staff.router)
app.include_router(ingredients.router)
app.include_router(recipes.router)
app.include_router(dashboard.router)

# 4. STARTUP LOGIC
@app.on_event("startup")
async def create_tables():
    """
    Ensures database tables exist. Works with the async engine 
    defined in your session.py.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Connection Successful: Database tables verified/created.")
    except Exception as e:
        print(f"❌ Database Error: {e}")

# 5. HEALTH CHECK ENDPOINT
@app.get("/")
async def root():
    return {
        "status": "online",
        "environment": "Production" if os.getenv("ALLOWED_ORIGINS") else "Development",
        "active_origins": ALLOWED_ORIGINS
    }

# 6. SERVER EXECUTION
if __name__ == "__main__":
    # Pull port from Docker 'PORT' env, or settings.PORT, or default 8000
    env_port = os.getenv("PORT")
    server_port = int(env_port) if env_port else getattr(settings, "PORT", 8000)
    
    print(f"🚀 Starting server on port {server_port}")
    uvicorn.run("main:app", host="0.0.0.0", port=server_port, reload=True)