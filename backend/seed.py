import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncGraphDatabase

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


async def seed_databases():
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client["social_network"]
    neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # 1. Nettoyage complet des deux bases
    await db["users"].delete_many({})
    await db["posts"].delete_many({})
    async with neo4j_driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")

    # 2. Insertion des utilisateurs (Synchronisation MongoDB + Neo4j)
    users = [
        {"_id": "u_alice", "username": "alice_g", "email": "alice@demo.fr", "full_name": "Alice Moreau", "bio": "Passionnée par Neo4j"},
        {"_id": "u_bob", "username": "bob_doc", "email": "bob@demo.fr", "full_name": "Bob Martin", "bio": "Architecte MongoDB"},
        {"_id": "u_claire", "username": "claire_ai", "email": "claire@demo.fr", "full_name": "Claire Dubois", "bio": "Data Engineer NoSQL"},
        {"_id": "u_david", "username": "david_ops", "email": "david@demo.fr", "full_name": "David Bernard", "bio": "DevOps & Docker"},
        {"_id": "u_emma", "username": "emma_dev", "email": "emma@demo.fr", "full_name": "Emma Petit", "bio": "Développeuse Fullstack"},
    ]

    async with neo4j_driver.session() as session:
        for u in users:
            # Insertion du document complet dans MongoDB
            await db["users"].insert_one({
                "_id": u["_id"],
                "username": u["username"],
                "email": u["email"],
                "password_hash": "$2b$12$demo_hash_placeholder",
                "profile": {"full_name": u["full_name"], "bio": u["bio"]},
                "stats": {"followers_count": 0, "following_count": 0},
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            # Création du nœud léger dans Neo4j
            await session.run(
                "MERGE (n:User {id: $id}) SET n.username = $username",
                id=u["_id"], username=u["username"]
            )

    # 3. Création des relations d'abonnement dans Neo4j
    # Alice suit Bob et Claire ; Bob suit David ; Claire suit Emma
    # -> Résultat attendu : David et Emma seront suggérés à Alice (niveau 2)
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

    # 4. Création de publications dans MongoDB
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

    print("Initialisation et peuplement des deux bases terminés !")
    mongo_client.close()
    await neo4j_driver.close()


if __name__ == "__main__":
    asyncio.run(seed_databases())