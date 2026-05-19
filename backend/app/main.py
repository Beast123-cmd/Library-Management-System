from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, books, transactions, users, dashboard, analytics
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-performance async backend for the SaaS Library Management System.",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# ---- CORS Middleware ----
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your deployed Vercel URL here when ready
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Register Routers ----
API_PREFIX = "/api/v1"
app.include_router(auth.router,         prefix=API_PREFIX)
app.include_router(books.router,        prefix=API_PREFIX)
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(users.router,        prefix=API_PREFIX)
app.include_router(dashboard.router,    prefix=API_PREFIX)
app.include_router(analytics.router,    prefix=API_PREFIX)


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "success",
        "message": "Library SaaS API is running.",
        "environment": settings.ENVIRONMENT
    }
