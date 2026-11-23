import uuid
import bcrypt
from fastapi import APIRouter, HTTPException
from pymongo.errors import DuplicateKeyError

from databases import db_state
from schemas import RegisterRequest, LoginRequest
from repositories.mongo_repo import MongoRepository
from repositories.neo4j_repo import Neo4jRepository

# Création du sous-routeur avec préfixe automatique /auth
router = APIRouter(prefix="/auth", tags=["Authentification"])


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


@router.post("/register", status_code=201)
async def register_user(payload: RegisterRequest):
    mongo = MongoRepository(db_state["mongo"])
    neo4j = Neo4jRepository(db_state["neo4j"])

    user_id = f"u_{uuid.uuid4().hex[:8]}"
    hashed_pwd = hash_password(payload.password)

    # 1. Insertion MongoDB
    try:
        user_doc = await mongo.create_user(
            user_id=user_id,
            username=payload.username,
            email=payload.email,
            password_hash=hashed_pwd,
            full_name=payload.full_name,
            bio=payload.bio,
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Ce nom d'utilisateur ou cette adresse e-mail est déjà utilisé.",
        )

    # 2. Création du nœud Neo4j (avec rollback MongoDB en cas d'erreur)
    try:
        await neo4j.create_user_node(user_id=user_id, username=payload.username)
    except Exception as exc:
        await mongo.delete_user(user_id)
        raise HTTPException(
            status_code=503,
            detail=f"Erreur lors de la création du nœud dans Neo4j : {str(exc)}",
        )

    return user_doc