import asyncpg


class _Postgresql:
    def __init__(self):
        self.pool = None

    async def get_pool(self):
        if self.pool is None:
            raise Exception("You should connect to database before making queries!")

        return self.pool

    async def connect(self, user, password, database, min_size, max_size):
        self.pool = await asyncpg.create_pool(
            user=user,
            password=password,
            database=database,
            min_size=min_size,
            max_size=max_size,
        )

db = _Postgresql()