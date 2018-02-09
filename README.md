# restycorn

Make fast, secure and restful API as simple as possible.

Example of usage:

```python
import asyncio
import asyncpgsa

import models
from pikabot_graphs import settings
from restycorn.restycorn.server import Server
from restycorn.restycorn.postgresql_read_only_resource import PostgreSQLReadOnlyResource


async def main():
    await asyncpgsa.pg.init(
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        database=settings.DATABASES['default']['NAME'],
        min_size=5,
        max_size=10,
    )

    server = Server('127.0.0.1')
    server.set_base_address('/api')

    server.register_resource('users', PostgreSQLReadOnlyResource(
        sqlalchemy_table=models.core_user,
        fields=('id', 'username', 'info', 'avatar_url', 'rating', 'comments_count', 'posts_count', 'hot_posts_count',
                'pluses_count', 'minuses_count', 'last_update_timestamp', 'subscribers_count', 'is_rating_ban',
                'updating_period', 'is_updated', 'pikabu_id', 'gender', 'approved', 'awards', 'signup_timestamp',),
        id_field='username',
        order_by=('id', 'rating', 'username', 'subscribers_count', 'comments_count', 'posts_count',
                  'hot_posts_count', 'pluses_count', 'minuses_count', 'last_update_timestamp', 'updating_period',
                  'pikabu_id', 'approved', 'signup_timestamp', ),
        search_by=('username', 'info', ),
        filter_by={
            'username': ('=', ),
            'rating': ('=', '>', '<'),
        },
        page_size=50,
    ))

    server.register_resource('communities', PostgreSQLReadOnlyResource(
        sqlalchemy_table=models.communities_app_community,
        fields=('id', 'url_name', 'name', 'description', 'avatar_url', 'background_image_url', 'subscribers_count',
                'stories_count', 'last_update_timestamp'),
        id_field='url_name',
        order_by=('id', 'subscribers_count', 'name', 'stories_count', 'last_update_timestamp', ),
        search_by=('url_name', 'name', 'description',),
        page_size=50,
    ))

    def register_graph_item_resource(resource_name, sqlalchemy_table):
        server.register_resource(resource_name, PostgreSQLReadOnlyResource(
            sqlalchemy_table=sqlalchemy_table,
            fields=('user_id', 'timestamp', 'value',),
            id_field='id',
            order_by=('id',),
            filter_by={
                'user_id': ('=',),
            },
            paginated=False,
        ))

    register_graph_item_resource('graph/user/rating', models.core_userratingentry)
    register_graph_item_resource('graph/user/subscribers', models.core_usersubscriberscountentry)
    register_graph_item_resource('graph/user/comments', models.core_usercommentscountentry)
    register_graph_item_resource('graph/user/posts', models.core_userpostscountentry)
    register_graph_item_resource('graph/user/hot_posts', models.core_userhotpostscountentry)
    register_graph_item_resource('graph/user/pluses', models.core_userplusescountentry)
    register_graph_item_resource('graph/user/minuses', models.core_userminusescountentry)

    return server


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.run_until_complete(main()).run()

```
