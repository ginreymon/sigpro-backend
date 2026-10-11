from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from apps.people.models import AuthUserEmployee, EmployeeLocal
from apps.user.views.auth_view import AuthViewSet

VIEW = "apps.user.views.auth_view"


class PasswordResetRequestTests(SimpleTestCase):

    def post(self, data):
        request = APIRequestFactory().post("/api/v1/auth/password-reset-request/", data, format="json")
        # The router applies the action's permission_classes (AllowAny); as_view does not.
        view = AuthViewSet.as_view({"post": "password_reset_request"}, permission_classes=[AllowAny])
        return view(request)

    def test_missing_params_answers_the_error_envelope(self):
        response = self.post({})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "missing_params")
        self.assertEqual(set(("detail", "code", "errors")) - set(response.data), set())

    @patch(f"{VIEW}.EmployeeLocal")
    def test_unknown_employee_gets_the_generic_answer(self, employee_model):
        employee_model.DoesNotExist = EmployeeLocal.DoesNotExist
        employee_model.objects.get.side_effect = EmployeeLocal.DoesNotExist

        response = self.post({"id_number": "1", "username": "x"})

        self.assertEqual((response.status_code, response.data), (200, {"message": "Datos inválidos"}))

    @patch(f"{VIEW}.AuthUserEmployee")
    @patch(f"{VIEW}.EmployeeLocal")
    def test_employee_without_account_gets_the_same_generic_answer_not_a_500(self, employee_model, link_model):
        employee_model.DoesNotExist = EmployeeLocal.DoesNotExist
        employee_model.objects.get.return_value = MagicMock()
        link_model.DoesNotExist = AuthUserEmployee.DoesNotExist
        link_model.objects.get.side_effect = AuthUserEmployee.DoesNotExist

        response = self.post({"id_number": "20586712", "username": "john.doe"})

        self.assertEqual((response.status_code, response.data), (200, {"message": "Datos inválidos"}))
