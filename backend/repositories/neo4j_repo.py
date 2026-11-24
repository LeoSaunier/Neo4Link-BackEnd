class Neo4jRepository:
    def __init__(self, driver):
        self.driver = driver

    async def create_user_node(self, user_id: str, username: str):
        """Crée le nœud pivot :User dans Neo4j lors de l'inscription."""
        query = """
        MERGE (u:User {id: $user_id})
        SET u.username = $username
        RETURN u.id AS id
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id, username=username)
            return await result.single()

    async def user_node_exists(self, user_id: str) -> bool:
        """Vérifie si le nœud :User existe dans Neo4j."""
        query = """
        MATCH (u:User {id: $user_id})
        RETURN count(u) > 0 AS exists
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id)
            record = await result.single()
            return record["exists"] if record else False