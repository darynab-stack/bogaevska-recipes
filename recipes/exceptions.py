from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


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
    return response
