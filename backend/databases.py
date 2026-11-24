import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)  # Charge les variables d'environnement depuis le fichier .env


db_state = {}

MONGO_URI = os.getenv("MONGO_URI")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialisation MongoDB avec le client asynchrone natif PyMongo
    print(MONGO_URI, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    mongo_client = AsyncMongoClient(MONGO_URI)
    db = mongo_client["social_network"]
    db_state["mongo"] = db
    
    existing_collections = await db.list_collection_names()
    if "users" not in existing_collections:
        await db.create_collection("users")
    if "posts" not in existing_collections:
        await db.create_collection("posts")

    # Pose des index MongoDB
    await db["users"].create_index("username", unique=True)
    await db["posts"].create_index([("author_id", 1), ("created_at", -1)])

    # 2. Initialisation Neo4j (Driver Bolt asynchrone)
    neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    db_state["neo4j"] = neo4j_driver

    # Pose de la contrainte d'unicité Cypher
    async with neo4j_driver.session() as session:
        await session.run(
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.id IS UNIQUE"
        )

    yield

    # 3. Fermeture propre (close() est asynchrone avec AsyncMongoClient)
    await mongo_client.close()
    await neo4j_driver.close()