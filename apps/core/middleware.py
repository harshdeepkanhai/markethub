import time
import logging

log = logging.getLogger(__name__)

class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        if duration > 1.0:  # Log only if the request took more than 1 second
            log.warning("SLOW %s %s %.2fs", request.method, request.path, duration)
        response["X-Response-Time"] = f"{duration:.3f}"
        return response