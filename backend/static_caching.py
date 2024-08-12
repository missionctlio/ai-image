from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
class CachedStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def get_response(self, path: str, scope: dict, receive: callable, send: callable) -> None:
        response = await super().get_response(path, scope, receive, send)
        if isinstance(response, Response):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        await response(scope, receive, send)