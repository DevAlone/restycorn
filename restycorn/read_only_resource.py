from restycorn.restycorn.base_resource import BaseResource

import abc

from restycorn.restycorn.exceptions import MethodIsNotAllowedException


class ReadOnlyResource(BaseResource):
    @abc.abstractmethod
    async def list(self) -> list:
        """
        It is called when client send GET request with url like this http://example.com/comments/
        Returns all items

        :return:
        """
        raise NotImplementedError()

    async def get(self, item_id) -> object:
        """
        Returns specific item with id = item_id, should return exception if item cannot be retrieved

        :param item_id: id of item to retrieve
        :return:
        """
        raise NotImplementedError()

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
