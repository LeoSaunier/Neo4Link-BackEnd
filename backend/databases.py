import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv



env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)  # Charge les variables d'environnement depuis le fichier .env


db_state = {}
import asyncio
import os
from datetime import datetime, timezone
import bcrypt
from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from neo4j import AsyncGraphDatabase

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)  # Charge les variables d'environnement depuis le fichier .env


MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "social_network")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Connexion avec le client asynchrone natif PyMongo et le driver Neo4j
    print(MONGO_URI, MONGO_DB_NAME, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    mongo_client = AsyncMongoClient(MONGO_URI)
    db = mongo_client[MONGO_DB_NAME]
    neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    existing_collections = await db.list_collection_names()
    if "users" not in existing_collections:
        await db.create_collection("users")
    if "posts" not in existing_collections:
        await db.create_collection("posts")

    # Pose des index MongoDB
    await db["users"].create_index("username", unique=True)
    await db["posts"].create_index([("author_id", 1), ("created_at", -1)])

    # 2. Nettoyage complet des deux bases
    await db["users"].delete_many({})
    await db["posts"].delete_many({})
    async with neo4j_driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")

    # 3. Insertion des utilisateurs (Synchronisation MongoDB + Neo4j)
    demo_hash = hash_password("password123")
    users = [
        {"_id": "u_alice", "username": "alice_g", "email": "alice@demo.fr", "full_name": "Alice Moreau",
         "bio": "Passionnée par Neo4j"},
        {"_id": "u_bob", "username": "bob_doc", "email": "bob@demo.fr", "full_name": "Bob Martin",
         "bio": "Architecte MongoDB"},
        {"_id": "u_claire", "username": "claire_ai", "email": "claire@demo.fr", "full_name": "Claire Dubois",
         "bio": "Data Engineer NoSQL"},
        {"_id": "u_david", "username": "david_ops", "email": "david@demo.fr", "full_name": "David Bernard",
         "bio": "DevOps & Docker"},
        {"_id": "u_emma", "username": "emma_dev", "email": "emma@demo.fr", "full_name": "Emma Petit",
         "bio": "Développeuse Fullstack"},
    ]

    async with neo4j_driver.session() as session:
        for u in users:
            # Insertion du document complet dans MongoDB
            await db["users"].insert_one({
                "_id": u["_id"],
                "username": u["username"],
                "email": u["email"],
                "password_hash": demo_hash,
                "profile": {"full_name": u["full_name"], "bio": u["bio"]},
                "stats": {"followers_count": 0, "following_count": 0},
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            # Création du nœud léger dans Neo4j
            await session.run(
                "MERGE (n:User {id: $id}) SET n.username = $username",
                id=u["_id"], username=u["username"]
            )

    # 4. Création des relations d'abonnement dans Neo4j
    # Alice suit Bob et Claire ; Bob suit David ; Claire suit Emma
    # -> Suggestions attendues pour Alice (niveau 2) : David et Emma
    follows = [
        ("u_alice", "u_bob"),
        ("u_alice", "u_claire"),
        ("u_bob", "u_david"),
        ("u_claire", "u_emma"),
    ]

    async with neo4j_driver.session() as session:
        for follower, target in follows:
            await session.run(
                """
                MATCH (a:User {id: $follower}), (b:User {id: $target})
                MERGE (a)-[r:FOLLOWS]->(b)
                SET r.since = datetime()
                """,
                follower=follower, target=target
            )
            await db["users"].update_one({"_id": follower}, {"$inc": {"stats.following_count": 1}})
            await db["users"].update_one({"_id": target}, {"$inc": {"stats.followers_count": 1}})

    # 5. Création de publications dans MongoDB
    posts = [
        {
            "_id": "p_001",
            "author_id": "u_bob",
            "author_snapshot": {"username": "bob_doc", "full_name": "Bob Martin"},
            "content": {"text": "MongoDB gère les documents polymorphes sans migration de schéma !"},
            "tags": ["mongodb", "nosql"],
            "likes": ["u_alice"],
            "comments": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "_id": "p_002",
            "author_id": "u_claire",
            "author_snapshot": {"username": "claire_ai", "full_name": "Claire Dubois"},
            "content": {"text": "Cypher rend les traversées à N degrés instantanées."},
            "tags": ["neo4j", "graph"],
            "likes": [],
            "comments": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
    await db["posts"].insert_many(posts)

    # Bien faire attention à sortir les données dans db_state pour les 2 bases
    db_state["mongo"] = db
    print("Initialisation et peuplement des deux bases terminés ! (Mot de passe démo : password123)")

    yield

    # Fermeture asynchrone obligatoire avec AsyncMongoClient
    await mongo_client.close()
    await neo4j_driver.close()