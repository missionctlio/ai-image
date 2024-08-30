from starlette.middleware.base import BaseHTTPMiddleware
import logging
import json

# Create a logger
logger = logging.getLogger('uvicorn.access')

class JSONLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Log the request
        request_body = await request.body()
        request_info = {
            "client_ip": request.client.host,
            "method": request.method,
            "url": str(request.url),
            "request_body": request_body.decode() if request_body else None
        }

        response = await call_next(request)
        
        # Log the response
        response_info = {
            "client_ip": request.client.host,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code
        }

        return response
