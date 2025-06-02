from django.http import JsonResponse
from django.utils.decorators import method_decorator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from core import settings
from modules.constants import TIMESTAMP_CACHE_TIMEOUT
from functools import wraps
from django.core.cache import cache


def cache_data(cache_key, timeout=TIMESTAMP_CACHE_TIMEOUT):
    """
    Decorator to cache data using a given key.

    :param cache_key: The key used to store the data in the cache.
    :param timeout: How long to cache the data (in seconds). Default is 5 minutes.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get the data from the cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                # If data is cached, return it
                return cached_data

            # If not cached, execute the function
            result = func(*args, **kwargs)

            # Cache the result with the provided key and timeout
            cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def check_api_key_decorator():
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            request = args[0]
            api_key = request.META.get("HTTP_X_API_KEY")
            if api_key is not None and api_key not in settings.API_KEY:
                return JsonResponse({"error": "Invalid API key"}, status=401)
            return view(*args, **kwargs)
        return wrapped_view
    return method_decorator(decorator)
