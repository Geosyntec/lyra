from typing import Any, Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute


class LyraRequest(Request):
    def relative_url_for(
        self, name: str, **path_params: Any
    ) -> str:  # pragma: no cover
        router = self.scope["router"]
        url_path = str(router.url_path_for(name, **path_params))
        return url_path


class LyraRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            request = LyraRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
