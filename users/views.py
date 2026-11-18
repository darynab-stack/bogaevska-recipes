import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from recipes.serializers import ErrorSerializer

from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    @extend_schema(
        tags=["Користувачі"],
        summary="Реєстрація",
        description="Доступно всім. Пароль зберігається лише у захешованому "
        "вигляді і не повертається у відповіді.",
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
            400: OpenApiResponse(
                ErrorSerializer, description="Дані не пройшли перевірку."
            ),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("Зареєстровано користувача %s (id=%s)", user.username, user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    @extend_schema(
        tags=["Користувачі"],
        summary="Вхід",
        description="Повертає access і refresh токени.",
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        logger.info("Користувач %s увійшов в акаунт", request.data.get("username"))
        return response


class RefreshView(TokenRefreshView):
    @extend_schema(
        tags=["Користувачі"],
        summary="Оновити access токен",
        description="Приймає refresh токен і повертає новий access токен.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Користувачі"],
        summary="Мій профіль",
        description="Потрібен access токен.",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(
                ErrorSerializer, description="Немає access токена або він недійсний."
            ),
        },
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
