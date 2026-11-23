from fastapi import FastAPI

# Création de l'instance principale de l'application
app = FastAPI(
    title="Polyglot Social Network API",
    description="API REST orchestrant MongoDB et Neo4j",
    version="1.0.0"
)

@app.get("/")
async def health_check():
    return {"status": "online", "databases": ["MongoDB", "Neo4j"]}