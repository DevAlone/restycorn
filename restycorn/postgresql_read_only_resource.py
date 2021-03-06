from pikabot_graphs import settings
from .postgresql import db
from .base_resource import BaseResource
from .exceptions import MethodIsNotAllowedException, ParamsValidationException, ResourceItemDoesNotExistException
from .postgresql_serializer import PostgreSQLSerializer
from .restycorn_types import uint

import asyncpgsa
import asyncpg
import re
import sqlalchemy
import time


class PostgreSQLReadOnlyResource(BaseResource):
    def __init__(self, sqlalchemy_table, fields, id_field, order_by, filter_by=None, search_by=None, paginated=True,
                 page_size=10, join=None):
        self.table = sqlalchemy_table
        self.fields = fields
        self.order_by_fields = order_by
        self.id_field = id_field
        self.search_by_fields = search_by if search_by is not None else []
        self.filter_by_fields = filter_by if filter_by is not None else []
        self.serializer = PostgreSQLSerializer(self.fields)
        self.paginated = paginated
        self.page_size = page_size
        self.join = join

    async def list(self, page: uint=0, order_by: str=None, search_text: str=None, filter: str=None, count: bool=False):
        if order_by is None:
            order_by = self.order_by_fields[0]

        order_by = order_by.strip()

        if (order_by[1:] if order_by.startswith('-') else order_by) not in self.order_by_fields:
            raise ParamsValidationException("It's not allowed to sort by this field")

        if order_by.startswith('-'):
            order_field_name = order_by[1:]
            descend_ordering = True
        else:
            order_field_name = order_by
            descend_ordering = False

        order_by = getattr(self.table.c, order_field_name)
        if descend_ordering:
            order_by = sqlalchemy.desc(order_by)

        # sql_request = self.table.select()
        if count:
            sql_request = sqlalchemy.select([sqlalchemy.func.count()])
        else:
            sql_request = sqlalchemy.select(['*'])

        select_table = self.table

        if self.join is not None:
            select_table = select_table.join(self.join[0], self.join[1])

        sql_request = sql_request.select_from(select_table)

        if search_text:
            search_text = search_text.strip()
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

        if not count:
            sql_request = sql_request.order_by(order_by)

        if self.paginated:
            sql_request = sql_request.limit(self.page_size)
            if page:
                sql_request = sql_request.offset(page * self.page_size)

        if settings.DEBUG:
            sql_request_str = str(sql_request).replace('\n', ' ')
            sql_params = sql_request.compile().params
            print("request: \"{}\"\nparams: \"{}\";".format(sql_request_str, sql_params))

        _debug_start_time = time.time()
        items = await asyncpgsa.pg.fetch(sql_request)
        _debug_end_start_time = time.time()

        time_to_process_request = _debug_end_start_time - _debug_start_time

        if time_to_process_request > 0.5:
            sql_request_str = str(sql_request).replace('\n', ' ')
            sql_params = sql_request.compile().params
            print("SLOW REQUEST: {}; with params: {};".format(sql_request_str, sql_params))
            print("Time to process request: {}".format(time_to_process_request))

        if count:
            return [], {
                'count': items[0][0],
            }

        return [self.serializer.serialize(item) for item in items]

    async def get(self, item_id: str) -> object:
        field = getattr(self.table.c, self.id_field)
        try:
            item_id = field.type.python_type(item_id)
        except ValueError:
            raise ParamsValidationException("Bad value for filter by field \"{}\"".format(field))

        sql_request = self.table.select().where(
            field == item_id
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
