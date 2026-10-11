import json

from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from rest_framework.exceptions import NotAuthenticated, NotFound, ValidationError

from core.exceptions import (
    ApiErrorEnvelopeMiddleware,
    api_exception_handler,
    api_not_found,
    api_server_error,
    build_error_body,
    error_response,
)


class BuildErrorBodyTests(SimpleTestCase):

    def test_field_errors_become_errors(self):
        body = build_error_body({"op_number": ["Debe ser un número entero."]}, 400)

        self.assertEqual(body["code"], "validation_error")
        self.assertEqual(body["detail"], "Debe ser un número entero.")
        self.assertEqual(body["errors"], {"op_number": ["Debe ser un número entero."]})
        self.assertEqual(set(body), {"detail", "code", "errors"})  # no legacy keys by default

    @override_settings(API_ERRORS_LEGACY_MIRROR=True)
    def test_field_errors_keep_form_keys_with_the_mirror_on(self):
        body = build_error_body({"op_number": ["Debe ser un número entero."]}, 400)
        self.assertEqual(body["op_number"], ["Debe ser un número entero."])

    def test_a_field_called_code_does_not_clash_with_the_envelope_code(self):
        body = build_error_body({"code": ["Ya existe un registro con este valor."]}, 400)

        self.assertEqual(body["code"], "validation_error")
        self.assertEqual(body["errors"], {"code": ["Ya existe un registro con este valor."]})

    def test_a_list_body_becomes_non_field_errors(self):
        body = build_error_body(["La jornada (sesión) ha expirado."], 400)

        self.assertEqual(body["errors"], {"non_field_errors": ["La jornada (sesión) ha expirado."]})
        self.assertEqual(body["detail"], "La jornada (sesión) ha expirado.")

    def test_legacy_error_key_becomes_the_detail(self):
        body = build_error_body({"error": "Credenciales inválidas"}, 401)

        self.assertEqual(body["detail"], "Credenciales inválidas")
        self.assertEqual(body["code"], "not_authenticated")
        self.assertEqual(body["errors"], {})
        self.assertNotIn("error", body)

    @override_settings(API_ERRORS_LEGACY_MIRROR=True)
    def test_legacy_keys_are_mirrored_when_the_switch_is_on(self):
        self.assertEqual(build_error_body({"error": "x"}, 401)["error"], "x")
        self.assertEqual(build_error_body({"message": "m"}, 400)["message"], "m")

    @override_settings(API_ERRORS_LEGACY_MIRROR=True)
    def test_integration_payload_keeps_its_own_keys_with_the_mirror_on(self):
        body = build_error_body({"ok": False, "error_type": 3, "details": ["a", "b"]}, 400)

        self.assertIs(body["ok"], False)
        self.assertEqual(body["error_type"], 3)
        self.assertEqual(body["details"], ["a", "b"])

    def test_jwt_style_body_keeps_its_code_and_has_no_field_errors(self):
        body = build_error_body(
            {"detail": "Token inválido", "code": "token_not_valid", "messages": [{"token_class": "AccessToken"}]},
            401,
        )

        self.assertEqual(body["code"], "token_not_valid")
        self.assertEqual(body["errors"], {})

    def test_already_standard_body_is_returned_untouched(self):
        data = {"detail": "x", "code": "y", "errors": {}}
        self.assertIs(build_error_body(data, 400), data)

    def test_default_detail_when_the_body_has_no_message(self):
        self.assertEqual(build_error_body({}, 404)["detail"], "No encontrado.")

    def test_mirror_is_off_by_default(self):
        body = build_error_body({"error": "x", "op_number": ["y"]}, 400)

        self.assertEqual(set(body), {"detail", "code", "errors"})
        self.assertEqual(body["errors"], {"op_number": ["y"]})

    def test_error_response_builds_the_envelope(self):
        response = error_response("Falta el parámetro", status_code=400, code="missing_params")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "missing_params")
        self.assertEqual(response.data["errors"], {})

    @override_settings(API_ERRORS_LEGACY_MIRROR=True)
    def test_error_response_mirrors_legacy_keys_when_the_switch_is_on(self):
        response = error_response("Credenciales inválidas", status_code=401, legacy={"error": "Credenciales inválidas"})

        self.assertEqual(response.data["error"], "Credenciales inválidas")
        self.assertEqual(response.data["detail"], "Credenciales inválidas")

    def test_error_response_has_only_the_envelope_by_default(self):
        response = error_response("x", legacy={"error": "x"})
        self.assertEqual(set(response.data), {"detail", "code", "errors"})

    def test_error_response_extra_data_is_always_kept(self):
        response = error_response(
            "SIESA rechazó el envío", status_code=422, code="siesa_rejected",
            extra={"submission_id": 7, "ok": False, "error_type": 3},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual((response.data["submission_id"], response.data["ok"], response.data["error_type"]), (7, False, 3))
        self.assertEqual(response.data["code"], "siesa_rejected")

    def test_error_response_with_field_errors_defaults_to_validation_error(self):
        response = error_response("Revisa los datos", errors={"register_ids": ["a"]})
        self.assertEqual(response.data["code"], "validation_error")
        self.assertEqual(response.data["errors"], {"register_ids": ["a"]})


class ExceptionHandlerTests(SimpleTestCase):

    def handle(self, exc):
        return api_exception_handler(exc, {"view": None, "request": None})

    def test_validation_error_dict(self):
        response = self.handle(ValidationError({"color": ["Este campo es requerido."]}))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "validation_error")
        self.assertEqual(response.data["errors"], {"color": ["Este campo es requerido."]})

    def test_validation_error_with_a_message(self):
        response = self.handle(ValidationError("No se encontró una actividad activa."))

        self.assertEqual(response.data["detail"], "No se encontró una actividad activa.")
        self.assertEqual(response.data["errors"], {"non_field_errors": ["No se encontró una actividad activa."]})

    def test_not_found_and_not_authenticated_codes(self):
        self.assertEqual(self.handle(NotFound()).data["code"], "not_found")
        unauthenticated = self.handle(NotAuthenticated())
        self.assertEqual((unauthenticated.status_code, unauthenticated.data["code"]), (401, "not_authenticated"))

    def test_unhandled_exceptions_are_left_to_django(self):
        self.assertIsNone(self.handle(RuntimeError("boom")))


class EnvelopeMiddlewareTests(SimpleTestCase):

    def run_middleware(self, response, path="/api/v1/production/modules/"):
        middleware = ApiErrorEnvelopeMiddleware(lambda request: response)
        return middleware(RequestFactory().get(path))

    def test_legacy_json_error_is_wrapped(self):
        response = self.run_middleware(JsonResponse({"error": "No data found"}, status=404))
        body = json.loads(response.content)

        self.assertEqual((body["detail"], body["code"], body["errors"]), ("No data found", "not_found", {}))
        self.assertNotIn("error", body)

    def test_standard_error_is_not_touched(self):
        original = JsonResponse({"detail": "x", "code": "y", "errors": {}}, status=400)
        content = original.content

        self.assertEqual(self.run_middleware(original).content, content)

    def test_success_responses_are_not_touched(self):
        response = self.run_middleware(JsonResponse({"error": "no es un error"}, status=200))
        self.assertEqual(json.loads(response.content), {"error": "no es un error"})

    def test_other_paths_and_non_json_are_not_touched(self):
        outside = self.run_middleware(JsonResponse({"error": "x"}, status=400), path="/admin/")
        self.assertEqual(json.loads(outside.content), {"error": "x"})

        html = HttpResponse("<h1>Not found</h1>", status=404)
        self.assertEqual(self.run_middleware(html).content, b"<h1>Not found</h1>")

    def test_content_length_is_updated(self):
        response = JsonResponse({"error": "x"}, status=400)
        response["Content-Length"] = str(len(response.content))

        wrapped = self.run_middleware(response)

        self.assertEqual(wrapped["Content-Length"], str(len(wrapped.content)))


class JsonErrorPagesTests(SimpleTestCase):

    def test_unknown_api_url_answers_the_envelope(self):
        response = api_not_found(RequestFactory().get("/api/v1/nope/"))
        body = json.loads(response.content)

        self.assertEqual(response.status_code, 404)
        self.assertEqual((body["code"], body["errors"]), ("not_found", {}))

    def test_server_error_on_api_does_not_leak_internals(self):
        response = api_server_error(RequestFactory().get("/api/v1/anything/"))
        body = json.loads(response.content)

        self.assertEqual(response.status_code, 500)
        self.assertEqual((body["detail"], body["code"]), ("Error interno del servidor.", "server_error"))

    def test_other_urls_keep_django_pages(self):
        response = api_not_found(RequestFactory().get("/admin/nope/"))
        self.assertIn("text/html", response["Content-Type"])