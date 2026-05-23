import json
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from apps.user.serializers import RegisterSerializer, ChangePasswordSerializer
from apps.production.models import EmployeeLocal
from apps.user.models import PasswordResetToken, UserEmployeeLink
from core.models.option import Option
from core.models.app_setting import AppSetting

HOME_CUSTOM_VIEW_SETTING = 'HOME_GRUPOS_VISTA_PERSONALIZADA'


class AuthViewSet(viewsets.ViewSet):

    def _resolve_home_view(self, group_ids: list) -> str:
        if not group_ids:
            return ''
        try:
            raw = AppSetting.objects.filter(
                name=HOME_CUSTOM_VIEW_SETTING,
                is_active=True,
            ).values_list('value', flat=True).first()
            if raw:
                mapping = json.loads(raw)  # { "ComponentKey": [id1, id2, ...] }
                for component_key, allowed_ids in mapping.items():
                    if any(gid in allowed_ids for gid in group_ids):
                        return component_key
        except (ValueError, TypeError):
            pass
        return ''

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path='register')
    def register(self, request):

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()          

            return Response(
                {
                    "user": serializer.data,
                    "user_id":user.id,
                    "rol": list(user.groups.values_list("name", flat=True))
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path='login')
    def login(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        if not password or not username:
            return Response(
                {"message": "Usuario y contraseña requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        groups = list(user.groups.values_list("name", flat=True))
        group_ids = list(user.groups.values_list("id", flat=True))
        refresh["username"] = user.username
        refresh["user_id"] = user.id
        refresh["groups"] = groups
        refresh["home_view"] = self._resolve_home_view(group_ids)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path='token/refresh')
    def refresh_token(self, request):

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token requerido"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)

            return Response({"access": str(refresh.access_token)})

        except TokenError:
            return Response(
                {"error": "Refresh token inválido o expirado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="change-password")
    def change_password(self, request):

        serializer = ChangePasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return Response(
                {"message": "Contraseña actual incorrecta"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if old_password == new_password:
            return Response(
                {"message": "La nueva contraseña no puede ser igual a la anterior"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response({"message": "Contraseña actualizada correctamente"})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="password-reset-request")
    def password_reset_request(self, request):

        id_number = request.data.get("id_number")
        username = request.data.get("username")

        if not id_number or not username:
            return Response(
                {"message": "Usuario y número de identificación requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            employee = EmployeeLocal.objects.get(id_number=id_number)
            link = UserEmployeeLink.objects.get(employee_local=employee)
            user = link.django_user        

            if user.username != username:
                raise EmployeeLocal.DoesNotExist()

            token_string = get_random_string(64)

            PasswordResetToken.objects.create(
                user=user,
                token=token_string,
                expires_at=timezone.now() + timedelta(minutes=15)
            )

            return Response({
                "reset_token": token_string,
                "expires_in_minutes": 15
            })

        except EmployeeLocal.DoesNotExist:
            return Response({
                "message": "Datos inválidos"
            })

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="password-reset-confirm")
    def password_reset_confirm(self, request):

        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return Response(
                {"message": "Token y contraseña requeridos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reset_token = PasswordResetToken.objects.get(token=token)

            if not reset_token.is_valid():
                return Response(
                    {"message": "Token expirado o usado"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = reset_token.user
            user.set_password(new_password)
            user.save()

            reset_token.is_used = True
            reset_token.save()

            return Response({"message": "Contraseña actualizada correctamente"})

        except PasswordResetToken.DoesNotExist:
            return Response(
                {"message": "Token inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="has-access")
    def has_access(self, request):
        user = request.user
        option_id = request.query_params.get("optionId")

        if not option_id:
            return Response(
                {"message": "optionId is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            option_id = int(option_id)
        except ValueError:
            return Response(
                {"message": "optionId must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_access = Option.objects.filter(
            id=option_id,
            state=True,
            module__state=True,
            group_options__group__in=user.groups.all(),
        ).exists()

        return Response({"optionId": option_id, "hasAccess": has_access})
