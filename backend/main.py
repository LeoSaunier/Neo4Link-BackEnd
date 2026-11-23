import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from databases import lifespan
from routers import auth, users, posts

app = FastAPI(
    title="Neo4Link Polyglot API",
    description="API REST orchestrant MongoDB et Neo4j",
    lifespan=lifespan,
)

# Configuration CORS
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des modules de routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)


@app.get("/", tags=["Santé"])
async def health_check():
    return {"status": "online", "architecture": "MongoDB + Neo4j"}