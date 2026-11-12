import logging

from django.http import Http404
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def error_response(detail, status_code, errors=None):
    return Response(
        {"detail": detail, "errors": errors or {}},
        status=status_code,
    )


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        response.data = {
            "detail": "Дані не пройшли перевірку. Виправте поля з помилками.",
            "errors": response.data,
        }
    elif isinstance(exc, NotAuthenticated):
        response.data = {
            "detail": "Потрібно увійти в акаунт. Передайте access токен "
            "у заголовку Authorization: Bearer <токен>.",
            "errors": {},
        }
    elif isinstance(exc, Http404):
        response.data = {
            "detail": "Об'єкт з таким id не знайдено.",
            "errors": {},
        }
    else:
        response.data = {
            "detail": response.data.get("detail", "Сталася помилка."),
            "errors": {},
        }

    request = context["request"]
    username = request.user.username or "гість"
    error_fields = ", ".join(response.data["errors"]) or "-"
    logger.warning(
        "%s %s -> %s (користувач: %s, поля з помилками: %s)",
        request.method,
        request.path,
        response.status_code,
        username,
        error_fields,
    )
    return response
