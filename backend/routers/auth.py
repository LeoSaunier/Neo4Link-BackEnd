import asyncio
import os
import uuid
import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pymongo.errors import DuplicateKeyError, PyMongoError

from databases import db_state, hash_password
from schemas import RegisterRequest, LoginRequest
from repositories.mongo_repo import MongoRepository
from repositories.neo4j_repo import Neo4jRepository

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)  # Charge les variables d'environnement depuis le fichier .env

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRE_HOURS = os.getenv("JWT_EXPIRE_HOURS")

# Création du sous-routeur avec préfixe automatique /auth
router = APIRouter(prefix="/auth", tags=["Authentification"])

def verify_password(password: str, stored_password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), stored_password_hash.encode("utf-8"))


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

@router.post("/login", status_code=200)
async def login_user(payload: LoginRequest):
    mongo = MongoRepository(db_state["mongo"])

    hashed_pwd = hash_password(payload.password)

    # 1. Récupération de l'utilisateur
    try:
        registered_user = await mongo.find_user_hashed_password(username=payload.username,
            password_hash=hashed_pwd,
        )

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="Service temporairement indisponible",
        )

    # Ici on met un faux mot de passe
    stored_password_hash = registered_user["password_hash"] if registered_user else "Fake_hash"
    password_ok = await asyncio.to_thread(verify_password, payload.password, stored_password_hash)

    if registered_user is None or not password_ok:
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects.",
        )

    # TODO : Ajouter le JWT et le token type {access_token, token_type, user_id}
    access_token = "generate the token with jwt now"
    return {"access_token": access_token, "token_type": "bearer", "user_id" : registered_user["_id"]}