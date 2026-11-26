from datetime import datetime, timezone
import uuid
from pymongo.errors import DuplicateKeyError
from pymongo import AsyncMongoClient


class MongoRepository:
    def __init__(self, db):
        self.users = db["users"]
        self.posts = db["posts"]

    async def create_user(
        self,
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        full_name: str,
        bio: str,
    ):
        doc = {
            "_id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "profile": {
                "full_name": full_name,
                "bio": bio,
            },
            "stats": {"followers_count": 0, "following_count": 0},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.users.insert_one(doc)

        # On retire le hash avant de renvoyer le document à l'API
        public_doc = {k: v for k, v in doc.items() if k != "password_hash"}
        return public_doc

    async def delete_user(self, user_id: str):
        """Utilisé uniquement pour le rollback si Neo4j échoue lors du register."""
        await self.users.delete_one({"_id": user_id})

    async def find_user_hashed_password(
        self,
        username: str,
        password_hash: str
    ):
        """
        Recherche l'utilisateur dans la base de données via son nom d'utilisateur (Unique) et mot de passe (Unique).
        Renvoie l'identifiant de l'utilisateur et le mot de passe hash stocké dans la base.
        """
        return await self.users.find_one({"username": username},{"password_hash": 1, "disabled": 1})