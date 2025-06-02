import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class BadRequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 400:
            logger.warning(
                f"Bad Request: {request.path} from {request.META.get('REMOTE_ADDR')}, "
                f"Method: {request.method}, "
                f"Body: {request.body.decode('utf-8', errors='ignore')}"
            )

        return response
