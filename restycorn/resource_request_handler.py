import inspect
import traceback

import aiohttp
import time
from aiohttp.web import json_response
from .base_resource import BaseResource
from .exceptions import ResourceItemDoesNotExistException, ParamsValidationException, MethodIsNotAllowedException


class ResourceRequestHandler:
    def __init__(self, resource: BaseResource):
        self.resource = resource

    async def request_resource(self, request: aiohttp.ClientRequest):
        kwargs = {}

        if request.method == 'GET' or request.method == 'OPTIONS':
            func = self.resource.list
        elif request.method == 'PUT':
            func = self.resource.replace_all
            kwargs = {'items': await request.json()}
        elif request.method == 'POST':
            func = self.resource.create,
            kwargs = {'items': await request.json()}
        elif request.method == 'DELETE':
            func = self.resource.delete_all
        else:
            return json_response({
                'status': 'error',
                'error_message': 'Method "{}" is not allowed here'.format(request.method)
            })

        return await self.pre_request(request, func, **kwargs)

    async def request_resource_item(self, request: aiohttp.ClientRequest):
        if 'id' not in request.match_info:
            return json_response({
                'status': 'error',
                'error_message': 'id is required',
            })

        item_id = request.match_info['id']

        kwargs = {}

        if request.method == 'GET' or request.method == 'OPTIONS':
            func = self.resource.get
            kwargs = {'item_id': item_id}
        elif request.method == 'PUT':
            func = self.resource.create_or_replace
            kwargs = {'item_id': item_id, 'item': await request.json()}
        elif request.method == 'PATCH':
            func = self.resource.update
            kwargs = {'item_id': item_id, 'item': await request.json()}
        elif request.method == 'DELETE':
            func = self.resource.delete
            kwargs = {'item_id': item_id}
        else:
            return json_response({
                'status': 'error',
                'error_message': 'Method "{}" is not allowed here'.format(request.method)
            })

        return await self.pre_request(request, func, **kwargs)

    _request_cache = {}
    async def pre_request(self, request, func, **kwargs):
        if self.resource.time_cached:
            cache_key = (
                request.method,
                str(request.url),
                func,
                frozenset(kwargs.items()),
            )

            if cache_key not in self._request_cache:
                self._request_cache[cache_key] = [
                    (await self.make_request(request, func, **kwargs)),
                    time.time() + self.resource.time_cache_seconds,
                ]

                if len(self._request_cache) > self.resource.time_cache_size:
                    self._request_cache.clear()

            response, expiration_time = self._request_cache[cache_key]

            if expiration_time < time.time():
                self._request_cache[cache_key] = (
                    (await self.make_request(request, func, **kwargs)),
                    time.time() + self.resource.time_cache_seconds
                )
        else:
            response = await self.make_request(request, func, **kwargs)

        response = json_response(response[0], status=response[1])

        if request.method == 'OPTIONS':
            headers = {
                "Allow": "GET, PUT, POST, DELETE"
            }
        else:
            headers = {}

        response.headers.update(headers)

        return response

    @staticmethod
    async def make_request(request, func, **kwargs) -> tuple:
        try:
            kwargs.update(dict(request.query))
            kwargs = ResourceRequestHandler._prepare_params(func, kwargs)

            result = await func(**kwargs)

            response = {
                'status': 'ok',
            }

            if type(result) is tuple:
                response['data'] = result[0]
                response.update(result[1])
            else:
                response['data'] = result

            return response, 200
        except ResourceItemDoesNotExistException:
            return {
                'status': 'error',
                'error_message': 'item does not exist',
            }, 404
        except MethodIsNotAllowedException:
            return {
                'status': 'error',
                'error_message': 'This method is not allowed for this resource',
            }, 404
        except ParamsValidationException as ex:
            return {
                'status': 'error',
                'error_message': str(ex),
            }, 400
        except BaseException as ex:
            print(type(ex))
            print(ex)
            traceback.print_exc()

            return {
                'status': 'error',
                'error_message': 'Error during processing resource "{}" with request method "{}"'.format(
                    request.url, request.method
                )
            }, 500

    @staticmethod
    def _prepare_params(func, params: dict) -> dict:
        signature = inspect.signature(func)
        signature_params = signature.parameters

        for key, val in params.items():
            if key not in signature_params:
                raise ParamsValidationException('key "{}" is not allowed here'.format(key))

        for param_name, parameter_info in signature_params.items():
            if param_name not in params and parameter_info.default is inspect.Parameter.empty:
                raise ParamsValidationException('param "{}" is required'.format(param_name))

        try:
            bind = signature.bind(**params)
        except TypeError:
            raise ParamsValidationException('Not enough params')

        bind.apply_defaults()

        result = bind.arguments

        for key, parameter_info in signature_params.items():
            if key in result:
                if parameter_info.annotation is inspect.Parameter.empty \
                        or (parameter_info.default is None and result[key] is None):
                    continue

                if type(result[key]) is not parameter_info.annotation:
                    try:
                        result[key] = parameter_info.annotation(result[key])
                    except ValueError:
                        raise ParamsValidationException('key "{}" should be "{}" or type convertible to "{}"'.format(
                            key, parameter_info.annotation, parameter_info.annotation))

        return result
