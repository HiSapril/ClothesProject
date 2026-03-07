import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import request_id_ctx, user_id_ctx

logger = logging.getLogger("app")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Generate or extract Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_ctx.set(request_id)
        
        # 2. Extract User ID (if already authenticated via dependency, might be tricky here, 
        # but we can check common headers or session if needed)
        # For now, we leave user_id to be set by the endpoint or auth dependency
        
        start_time = time.time()
        
        # 3. Log Request Start
        logger.info(f"Started {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # 4. Add Request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # SILENCE: Only log if it's an error or a state-changing POST/DELETE request
            # This drastically reduces terminal noise during polling
            if response.status_code >= 400 or request.method in ["POST", "DELETE", "PUT"]:
                process_time = (time.time() - start_time) * 1000
                logger.info(
                    f"Completed {request.method} {request.url.path} - "
                    f"Status: {response.status_code} - Duration: {process_time:.2f}ms"
                )
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Failed {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {process_time:.2f}ms",
                exc_info=True
            )
            raise
