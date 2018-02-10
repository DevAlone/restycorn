import asyncio

import asyncpg
import sqlalchemy
import asyncpgsa
from sqlalchemy import Table

from restycorn.base_resource import BaseResource
from restycorn.postgresql_read_only_resource import PostgreSQLReadOnlyResource
from restycorn.server import Server
from restycorn.exceptions import ResourceItemDoesNotExistException
from restycorn.postgresql_serializer import PostgreSQLSerializer


class TestResource(BaseResource):
    def __init__(self):
        self.db = {}
        self.last_id = 0
        self.metadata = sqlalchemy.MetaData()
        self.table = sqlalchemy.Table(
            'core_userratingentry', self.metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('user_id', sqlalchemy.Integer),
            sqlalchemy.Column('timestamp', sqlalchemy.Integer),
            sqlalchemy.Column('value', sqlalchemy.Integer),
        )
        self.serializer = PostgreSQLSerializer(['id', 'user_id', 'timestamp', 'value'])

    async def list(self) -> list:
        # global db
        # pool = await db.get_pool()
        value = 10

        sql_request = self.table.select().where(
            sqlalchemy.and_(
                self.table.c.user_id == value,
                self.table.c.timestamp > 0,
            )
        ).order_by(self.table.c.timestamp).limit(10)
        print(str(sql_request))
        print(sql_request.compile().params)

        items = await asyncpgsa.pg.fetch(sql_request)

        return [self.serializer.serialize(item) for item in items]
        #
        # async with pool.acquire() as connection:
        #     items = await connection.fetch(str(sql_request), sql_request.compile().params)
        #
        #     return [self.serializer.serialize(item) for item in items]

    async def replace_all(self, items: list):
        self.db = {}
        for item in items:
            self.create(item)

    async def create(self, item) -> object:
        self.last_id += 1
        self.db[self.last_id] = item

        return self.db[self.last_id]

    async def delete_all(self):
        self.db.clear()

    async def get(self, item_id) -> object:
        item_id = int(item_id)
        if item_id not in self.db:
            raise ResourceItemDoesNotExistException()

        return self.db[item_id]

    async def create_or_replace(self, item_id, item: dict) -> object:
        self.db[item_id] = item
        return self.db[item_id]

    async def update(self, item_id, item: dict) -> object:
        for key, val in item:
            setattr(self.db[item_id], key, val)

        return self.db[item_id]

    async def delete(self, item_id):
        del self.db[item_id]


async def main():
    await asyncpgsa.pg.init(
        user='test',
        password='test',
        database='test',
        min_size=5,
        max_size=10,
    )

    server = Server()
    server.set_base_address('/api')

    metadata = sqlalchemy.MetaData()

    server.register_resource('test', TestResource())

    server.register_resource('users', PostgreSQLReadOnlyResource(
        sqlalchemy_table=Table(
            'core_user', metadata,
            sqlalchemy.Column('id', sqlalchemy.BigInteger, primary_key=True),
            sqlalchemy.Column('username', sqlalchemy.String),
            sqlalchemy.Column('info', sqlalchemy.String),
            sqlalchemy.Column('avatar_url', sqlalchemy.String),
            sqlalchemy.Column('rating', sqlalchemy.Integer),
            sqlalchemy.Column('comments_count', sqlalchemy.Integer),
            sqlalchemy.Column('posts_count', sqlalchemy.Integer),
            sqlalchemy.Column('hot_posts_count', sqlalchemy.Integer),
            sqlalchemy.Column('pluses_count', sqlalchemy.Integer),
            sqlalchemy.Column('minuses_count', sqlalchemy.Integer),
            sqlalchemy.Column('last_update_timestamp', sqlalchemy.BigInteger),
            sqlalchemy.Column('subscribers_count', sqlalchemy.Integer),
            sqlalchemy.Column('is_rating_ban', sqlalchemy.Boolean),
            sqlalchemy.Column('updating_period', sqlalchemy.Integer),
            sqlalchemy.Column('is_updated', sqlalchemy.Boolean),
            sqlalchemy.Column('pikabu_id', sqlalchemy.BigInteger),
            sqlalchemy.Column('gender', sqlalchemy.String(1)),
            sqlalchemy.Column('approved', sqlalchemy.String),
            sqlalchemy.Column('awards', sqlalchemy.String),
            sqlalchemy.Column('signup_timestamp', sqlalchemy.BigInteger),
        ),
        fields=('id', 'username', 'info', 'avatar_url', 'rating', 'comments_count', 'posts_count', 'hot_posts_count',
                'pluses_count', 'minuses_count', 'last_update_timestamp', 'subscribers_count', 'is_rating_ban',
                'updating_period', 'is_updated', 'pikabu_id', 'gender', 'approved', 'awards', 'signup_timestamp',),
        id_field='username',
        order_by=(
            'id',
            'rating',
            'username',
            'subscribers_count',
            'comments_count',
            'posts_count',
            'hot_posts_count',
            'pluses_count',
            'minuses_count',
            'last_update_timestamp',
            'updating_period',
            'pikabu_id',
            'approved',
            'signup_timestamp',
        ),
        search_by=('username', 'info', ),
        filter_by={
            'username': ('=', ),
            'rating': ('=', '>', '<'),
        },
        page_size=50,
    ))

    server.register_resource('communities', PostgreSQLReadOnlyResource(
        sqlalchemy_table=Table(
            'communities_app_community', metadata,
            sqlalchemy.Column('id', sqlalchemy.BigInteger, primary_key=True),
            sqlalchemy.Column('url_name', sqlalchemy.String),
            sqlalchemy.Column('name', sqlalchemy.String),
            sqlalchemy.Column('description', sqlalchemy.String),
            sqlalchemy.Column('avatar_url', sqlalchemy.String),
            sqlalchemy.Column('background_image_url', sqlalchemy.String),
            sqlalchemy.Column('subscribers_count', sqlalchemy.Integer),
            sqlalchemy.Column('stories_count', sqlalchemy.Integer),
            sqlalchemy.Column('last_update_timestamp', sqlalchemy.BigInteger),
        ),
        fields=('id', 'url_name', 'name', 'description', 'avatar_url', 'background_image_url', 'subscribers_count',
                'stories_count', 'last_update_timestamp'),
        id_field='url_name',
        order_by=(
            'id',
            'subscribers_count',
            'name',
            'stories_count',
            'last_update_timestamp',
        ),
        search_by=('url_name', 'name', 'description',),
        page_size=50,
    ))

    server.register_resource('graph/user/rating', PostgreSQLReadOnlyResource(
        sqlalchemy_table=Table(
            'core_userratingentry', metadata,
            sqlalchemy.Column('id', sqlalchemy.BigInteger, primary_key=True),
            sqlalchemy.Column('user_id', sqlalchemy.BigInteger),
            sqlalchemy.Column('timestamp', sqlalchemy.BigInteger),
            sqlalchemy.Column('value', sqlalchemy.Integer),
        ),
        fields=('user_id', 'timestamp', 'value', ),
        id_field='id',
        order_by=('id', ),
        filter_by={
            'user_id': ('=', ),
        },
        paginated=False,
    ))

    communities_app_communitycountersentry = Table(
        'communities_app_communitycountersentry', metadata,
        sqlalchemy.Column('id', sqlalchemy.BigInteger, primary_key=True),
        sqlalchemy.Column('timestamp', sqlalchemy.BigInteger),
        sqlalchemy.Column('community_id', sqlalchemy.BigInteger),
        sqlalchemy.Column('subscribers_count', sqlalchemy.Integer),
        sqlalchemy.Column('stories_count', sqlalchemy.Integer),
    )

    def register_community_graph_item_resource(resource_name):
        server.register_resource('graph/community/' + resource_name, PostgreSQLReadOnlyResource(
            sqlalchemy_table=communities_app_communitycountersentry,
            fields=('timestamp', '{} as value'.format(resource_name)),
            id_field='community_id',
            order_by=('id',),
            filter_by={
                'community_id': ('=',),
            },
            paginated=False,
        ))

    register_community_graph_item_resource('subscribers_count')
    register_community_graph_item_resource('stories_count')

    return server


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.run_until_complete(main()).run()
