from django.conf import settings
from django.middleware.csrf import get_token
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
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
from apps.people.models import AuthUserEmployee, EmployeeLocal
from apps.user.models import PasswordResetToken
from core.models.option import Option
from core.exceptions import error_response
from core.models.role_home_view import RoleHomeView
from core.permissions import has_option_access


def _set_refresh_cookie(response, refresh_token: str):
    """Stores the refresh token in an HttpOnly cookie scoped to the auth endpoints."""
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=settings.REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )


def _delete_refresh_cookie(response):
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def _enforce_csrf(request):
    """Double-submit CSRF check (csrftoken cookie + X-CSRFToken header); raises 403 on failure."""
    SessionAuthentication().enforce_csrf(request)


class AuthViewSet(viewsets.ViewSet):

    def _resolve_home_view(self, group_ids: list) -> str:
        if not group_ids:
            return ''
        link = RoleHomeView.objects.filter(
            group_id__in=group_ids, is_active=True, home_view__is_active=True
        ).select_related('home_view').first()
        return link.home_view.key if link else ''

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path='register')
    def register(self, request):

        if not has_option_access(request.user, "users"):
            return error_response(
                "No tiene permisos para realizar esta acción.", status_code=status.HTTP_403_FORBIDDEN,
                code="permission_denied", legacy={"message": "No tiene permisos para realizar esta acción."},
            )

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "user": serializer.data,
                "user_id":user.id,
                "rol": list(user.groups.values_list("name", flat=True))
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path='login')
    def login(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        if not password or not username:
            return error_response(
                "Usuario y contraseña requeridos", code="missing_credentials",
                legacy={"message": "Usuario y contraseña requeridos"},
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return error_response(
                "Credenciales inválidas", status_code=status.HTTP_401_UNAUTHORIZED,
                code="invalid_credentials", legacy={"error": "Credenciales inválidas"},
            )

        refresh = RefreshToken.for_user(user)

        groups = list(user.groups.values_list("name", flat=True))
        group_ids = list(user.groups.values_list("id", flat=True))
        refresh["username"] = user.username
        refresh["user_id"] = user.id
        refresh["groups"] = groups
        refresh["home_view"] = self._resolve_home_view(group_ids)

        # DUAL MODE: the refresh token is also returned in the body for clients that still
        # keep it in localStorage. Remove "refresh" from the body once they are migrated.
        response = Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )
        _set_refresh_cookie(response, str(refresh))
        get_token(request._request)  # makes the CSRF middleware set the csrftoken cookie
        return response

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path='token/refresh')
    def refresh_token(self, request):

        # The cookie takes precedence; the body is the DUAL MODE fallback for legacy clients.
        cookie_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        from_cookie = bool(cookie_token)
        refresh_token = cookie_token or request.data.get("refresh")

        if not refresh_token:
            return error_response(
                "Refresh token requerido", code="missing_refresh_token",
                legacy={"error": "Refresh token requerido"},
            )

        # Only a cookie is sent automatically by the browser, so only it needs CSRF protection.
        if from_cookie:
            _enforce_csrf(request)

        try:
            refresh = RefreshToken(refresh_token)
            access = str(refresh.access_token)

            # ROTATE_REFRESH_TOKENS: issue a new refresh token on every refresh.
            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            data = {"access": access}
            if not from_cookie:
                data["refresh"] = str(refresh)  # legacy clients store it themselves

            response = Response(data)
            _set_refresh_cookie(response, str(refresh))  # also migrates legacy clients to the cookie
            get_token(request._request)
            return response

        except TokenError:
            response = error_response(
                "Refresh token inválido o expirado", status_code=status.HTTP_401_UNAUTHORIZED,
                code="invalid_refresh_token", legacy={"error": "Refresh token inválido o expirado"},
            )
            _delete_refresh_cookie(response)
            return response

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path='logout')
    def logout(self, request):
        # Only clears the cookie, so it needs neither authentication nor CSRF protection.
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _delete_refresh_cookie(response)
        return response

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="change-password")
    def change_password(self, request):

        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not user.check_password(old_password):
            return error_response(
                "Contraseña actual incorrecta", code="wrong_password",
                legacy={"message": "Contraseña actual incorrecta"},
            )

        if old_password == new_password:
            return error_response(
                "La nueva contraseña no puede ser igual a la anterior", code="same_password",
                legacy={"message": "La nueva contraseña no puede ser igual a la anterior"},
            )

        user.set_password(new_password)
        user.save()

        return Response({"message": "Contraseña actualizada correctamente"})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="password-reset-request")
    def password_reset_request(self, request):

        id_number = request.data.get("id_number")
        username = request.data.get("username")

        if not id_number or not username:
            return error_response(
                "Usuario y número de identificación requeridos", code="missing_params",
                legacy={"message": "Usuario y número de identificación requeridos"},
            )

        try:
            employee = EmployeeLocal.objects.get(id_number=id_number)
            link = AuthUserEmployee.objects.get(employee_local=employee)
            user = link.auth_user

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

        except (EmployeeLocal.DoesNotExist, AuthUserEmployee.DoesNotExist):
            # Same answer whether the employee does not exist or has no account, so the
            # endpoint does not reveal which employees have one (and never answers 500).
            return Response({
                "message": "Datos inválidos"
            })

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="password-reset-confirm")
    def password_reset_confirm(self, request):

        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return error_response(
                "Token y contraseña requeridos", code="missing_params",
                legacy={"message": "Token y contraseña requeridos"},
            )

        try:
            reset_token = PasswordResetToken.objects.get(token=token)

            if not reset_token.is_valid():
                return error_response(
                    "Token expirado o usado", code="token_expired",
                    legacy={"message": "Token expirado o usado"},
                )

            user = reset_token.user
            user.set_password(new_password)
            user.save()

            reset_token.is_used = True
            reset_token.save()

            return Response({"message": "Contraseña actualizada correctamente"})

        except PasswordResetToken.DoesNotExist:
            return error_response(
                "Token inválido", code="invalid_token",
                legacy={"message": "Token inválido"},
            )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="has-access")
    def has_access(self, request):
        user = request.user
        option_id = request.query_params.get("optionId")

        if not option_id:
            return error_response(
                "optionId is required", code="missing_params",
                legacy={"message": "optionId is required"},
            )

        try:
            option_id = int(option_id)
        except ValueError:
            return error_response(
                "optionId must be an integer", code="invalid_param",
                legacy={"message": "optionId must be an integer"},
            )

        has_access = Option.objects.filter(
            id=option_id,
            state=True,
            module__state=True,
            group_options__group__in=user.groups.all(),
        ).exists()

        return Response({"optionId": option_id, "hasAccess": has_access})
