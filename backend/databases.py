import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncGraphDatabase

# Conteneur global partagé par toutes les routes
db_state = {}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 1. INITIALISATION MONGODB ---
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client["social_network"]
    db_state["mongo"] = db

    # Création explicite des collections si inexistantes
    collections = await db.list_collection_names()
    if "users" not in collections:
        await db.create_collection("users")
    if "posts" not in collections:
        await db.create_collection("posts")

    # Pose des index critiques (unicité du login + rapidité du feed)
    await db["users"].create_index("username", unique=True)
    await db["users"].create_index("email", unique=True)
    await db["posts"].create_index([("author_id", 1), ("created_at", -1)])
    await db["posts"].create_index("tags")

    # --- 2. INITIALISATION NEO4J ---
    neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    db_state["neo4j"] = neo4j_driver

    # Pose des contraintes Cypher (génère automatiquement les index associés)
    async with neo4j_driver.session() as session:
        await session.run(
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.id IS UNIQUE"
        )
        await session.run(
            "CREATE INDEX user_username_idx IF NOT EXISTS "
            "FOR (u:User) ON (u.username)"
        )

    yield  # L'API est prête à recevoir des requêtes

    # --- 3. FERMETURE PROPRE ---
    mongo_client.close()
    await neo4j_driver.close()