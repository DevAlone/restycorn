from aiohttp import web

from .base_resource import BaseResource

from .resource_request_handler import ResourceRequestHandler


class Server:
    def __init__(self, host: str="localhost", port: int=4444, access_log_format=None):
        if port < 0 or port > 65535:
            raise ValueError("Port should be in range 0 - 65535")

        self.host = host
        self.port = port
        self.base_address = '/'
        self.app = web.Application()
        self.access_log_format = access_log_format
        self.pre_request_function = None
        self.default_handler = None

    def run(self):
        if self.default_handler is not None:
            self.app.router.add_route(
                'GET',
                '/{tail:.*}',
                lambda *args, **kwargs: self.request_handler(handler=self.default_handler, *args, **kwargs)
            )

        web.run_app(self.app, host=self.host, port=self.port, access_log_format=self.access_log_format)

    def register_resource(self, resource_name, resource: BaseResource):
        handler = ResourceRequestHandler(resource)
        resource_url = self.base_address + '/' + resource_name

        self.app.router.add_route(
            '*',
            resource_url,
            lambda *args, **kwargs: self.request_handler(handler=handler.request_resource, *args, **kwargs)
        )
        self.app.router.add_route(
            '*',
            resource_url + '/',
            lambda *args, **kwargs: self.request_handler(handler=handler.request_resource, *args, **kwargs)
        )
        self.app.router.add_route(
            '*',
            resource_url + '/{id}',
            lambda *args, **kwargs: self.request_handler(handler=handler.request_resource_item, *args, **kwargs)
        )

    def set_base_address(self, base_address: str):
        self.base_address = base_address

    async def request_handler(self, request, handler):
        if self.pre_request_function:
            pre_result = await self.pre_request_function(request)
            if pre_result is not None:
                return pre_result

        return await handler(request)

    def set_default_route(self, handler):
        self.default_handler = handler
