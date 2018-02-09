import asyncpgsa
import re
import sqlalchemy

from .base_resource import BaseResource
from .exceptions import MethodIsNotAllowedException, ParamsValidationException, ResourceItemDoesNotExistException
from .postgresql_serializer import PostgreSQLSerializer
from .restycorn_types import uint


class PostgreSQLReadOnlyResource(BaseResource):
    def __init__(self, sqlalchemy_table, fields, id_field, order_by, filter_by=None, search_by=None, paginated=True,
                 page_size=10):
        self.table = sqlalchemy_table
        self.fields = fields
        self.order_by_fields = order_by
        self.id_field = id_field
        self.search_by_fields = search_by if search_by is not None else []
        self.filter_by_fields = filter_by if filter_by is not None else []
        self.serializer = PostgreSQLSerializer(self.fields)
        self.paginated = paginated
        self.page_size = page_size

    async def list(self, page: uint=0, order_by: str=None, search_text: str=None, filter: str=None) -> list:
        if order_by is None:
            order_by = self.order_by_fields[0]

        order_by = order_by.strip()

        if (order_by[1:] if order_by.startswith('-') else order_by) not in self.order_by_fields:
            raise ParamsValidationException("It's not allowed to sort by this field")

        sql_request = self.table.select()

        if search_text:
            search_text = \
                '%' + search_text.replace('!', '!!').replace("%", "!%").replace("_", "!_").replace("[", "![") + '%'

            conditions = []
            for search_field in self.search_by_fields:
                conditions.append(getattr(self.table.c, search_field).ilike(search_text))

            sql_request = sql_request.where(sqlalchemy.or_(*conditions))

        if filter:
            for expr in filter.split('&&'):
                match = re.match('([a-zA-Z0-9_]+)\s*?([><=])\s*?([a-zA-Z0-9_]+)', expr.strip())
                if not match:
                    raise ParamsValidationException("Bad filter expression")

                field, operator, value = match.groups()

                if field not in self.filter_by_fields:
                    raise ParamsValidationException("It's not allowed to filter by this field")

                if operator not in self.filter_by_fields[field]:
                    raise ParamsValidationException("It's not allowed to filter by this field using this operator")

                field = getattr(self.table.c, field)

                try:
                    value = field.type.python_type(value)
                except ValueError:
                    raise ParamsValidationException("Bad value for filter by field \"{}\"".format(field))

                if operator == '=':
                    sql_request = sql_request.where(field == value)
                elif operator == '>':
                    sql_request = sql_request.where(field > value)
                elif operator == '<':
                    sql_request = sql_request.where(field < value)
                else:
                    raise ParamsValidationException("It's not allowed to filter using this operator")

        sql_request = sql_request.order_by(order_by)

        if self.paginated:
            sql_request = sql_request.limit(self.page_size)
            if page:
                sql_request = sql_request.offset(self.page_size)

        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('request: "{}"'.format(sql_request))
        print('params: "{}"'.format(sql_request.compile().params))
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

        items = await asyncpgsa.pg.fetch(sql_request)

        return [self.serializer.serialize(item) for item in items]

    async def get(self, item_id: str) -> object:
        sql_request = self.table.select(self.fields).where(
            self.id_field == item_id
        )

        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('request: "{}"'.format(sql_request))
        print('params: "{}"'.format(sql_request.compile().params))
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

        item = await asyncpgsa.pg.fetchrow(sql_request)

        if item is None:
            raise ResourceItemDoesNotExistException()

        return self.serializer.serialize(item)

    async def replace_all(self, items: list):
        raise MethodIsNotAllowedException()

    async def create(self, item) -> object:
        raise MethodIsNotAllowedException()

    async def delete_all(self):
        raise MethodIsNotAllowedException()

    async def create_or_replace(self, item_id, item: dict) -> object:
        raise MethodIsNotAllowedException()

    async def update(self, item_id, item: dict) -> object:
        raise MethodIsNotAllowedException()

    async def delete(self, item_id):
        raise MethodIsNotAllowedException()
