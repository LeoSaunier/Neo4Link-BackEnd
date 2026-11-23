import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from databases import lifespan, db_state
from repositories.mongo_repo import MongoRepository
from repositories.neo4j_repo import Neo4jRepository

app = FastAPI(title="Neo4Link Polyglot API", lifespan=lifespan)

# Récupération des origines autorisées (Vite dev + Docker frontend)
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)