from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.production.services import work_break_service, work_session_service
from apps.production.services.exceptions import SessionRuleError
from apps.production.views.session_rule_error_mixin import SessionRuleErrorMixin

BREAK_SERVICE = "apps.production.services.work_break_service"
SESSION_SERVICE = "apps.production.services.work_session_service"


def make_activity(*, is_active=True, session_closed=False, is_paused=False, active_break=None):
    return SimpleNamespace(
        is_active=is_active,
        work_session=SimpleNamespace(is_closed=session_closed),
        is_paused=is_paused,
        active_break=active_break,
    )


class PauseRulesTests(SimpleTestCase):

    def pause(self, activity=None, **overrides):
        kwargs = dict(work_break_id=None, custom_reason="Reunion", work_break_minutes=None, auto_resume=False)
        kwargs.update(overrides)
        return work_break_service.pause(activity or make_activity(), "user", **kwargs)

    def assert_error(self, expected_detail, status_code=400, **kwargs):
        with self.assertRaises(SessionRuleError) as ctx:
            self.pause(**kwargs)
        self.assertEqual(ctx.exception.payload, {"detail": expected_detail})
        self.assertEqual(ctx.exception.status_code, status_code)

    def test_inactive_activity(self):
        self.assert_error("La actividad no está activa.", activity=make_activity(is_active=False))

    def test_closed_session(self):
        self.assert_error("La jornada (sesión) está cerrada.", activity=make_activity(session_closed=True))

    def test_already_paused_without_end(self):
        self.assert_error(
            "La actividad ya está pausada. Debes reanudarla para continuar.",
            activity=make_activity(is_paused=True, active_break=SimpleNamespace(end_time=None)),
        )

    def test_already_paused_reports_remaining_minutes(self):
        active_break = SimpleNamespace(end_time=timezone.now() + timedelta(minutes=5, seconds=30))
        self.assert_error(
            "La actividad está pausada. Faltan 6 minuto(s) para reanudar.",
            activity=make_activity(is_paused=True, active_break=active_break),
        )

    def test_already_paused_when_break_time_is_over(self):
        active_break = SimpleNamespace(end_time=timezone.now() - timedelta(minutes=1))
        self.assert_error(
            "El tiempo de pausa ya terminó. Reanuda la actividad para continuar.",
            activity=make_activity(is_paused=True, active_break=active_break),
        )

    def test_needs_break_type_or_reason(self):
        self.assert_error(
            "Debe indicar un tipo de pausa o un motivo personalizado.", custom_reason=None,
        )

    def test_auto_resume_with_custom_reason_needs_minutes(self):
        self.assert_error(
            "Debe indicar work_break_minutes para calcular el auto-resume del motivo personalizado.",
            auto_resume=True,
        )

    def test_minutes_must_be_integer(self):
        self.assert_error("Los minutos deben ser un número entero.", work_break_minutes="abc")

    def test_minutes_must_be_positive(self):
        self.assert_error("Los minutos deben ser mayores a 0.", work_break_minutes=0)

    @patch(f"{BREAK_SERVICE}.WorkSessionActivityRepository")
    def test_unknown_break_type_is_404(self, repository):
        repository.find_work_break.return_value = None
        self.assert_error("El tipo de pausa no existe.", status_code=404, work_break_id=99, custom_reason=None)

    @patch(f"{BREAK_SERVICE}.transaction")
    @patch(f"{BREAK_SERVICE}.WorkBreakRecord")
    @patch(f"{BREAK_SERVICE}.WorkSessionActivityRepository")
    def test_custom_reason_with_minutes_sets_end_time(self, repository, record_class, _transaction):
        record = record_class.return_value
        record.end_time = None

        result = self.pause(custom_reason="  Reunion  ", work_break_minutes="15")

        self.assertIs(result, record)
        self.assertEqual(record_class.call_args.kwargs["custom_reason"], "Reunion")
        self.assertIsNotNone(record.end_time)
        repository.save_break_record.assert_called_once_with(record)

    @patch(f"{BREAK_SERVICE}.transaction")
    @patch(f"{BREAK_SERVICE}.WorkBreakRecord")
    @patch(f"{BREAK_SERVICE}.WorkSessionActivityRepository")
    def test_auto_resume_saves_twice_and_resumes_at_end_time(self, repository, record_class, _transaction):
        record = record_class.return_value
        record.end_time = None

        self.pause(work_break_minutes=10, auto_resume=True)

        self.assertEqual(repository.save_break_record.call_count, 2)
        self.assertEqual(record.resumed_at, record.end_time)


class ResumeRulesTests(SimpleTestCase):

    def test_not_paused(self):
        with self.assertRaises(SessionRuleError) as ctx:
            work_break_service.resume(make_activity(active_break=None))
        self.assertEqual(ctx.exception.payload, {"detail": "La actividad no está pausada."})

    @patch(f"{BREAK_SERVICE}.WorkSessionActivityRepository")
    def test_custom_break_gets_end_time_on_resume(self, repository):
        active_break = SimpleNamespace(work_break_id=None, end_time=None, resumed_at=None)

        result = work_break_service.resume(make_activity(active_break=active_break))

        self.assertIs(result, active_break)
        self.assertIsNotNone(active_break.resumed_at)
        self.assertEqual(active_break.end_time, active_break.resumed_at)
        repository.save_break_record.assert_called_once_with(active_break)

    @patch(f"{BREAK_SERVICE}.WorkSessionActivityRepository")
    def test_typed_break_keeps_its_end_time(self, repository):
        planned_end = timezone.now() + timedelta(minutes=10)
        active_break = SimpleNamespace(work_break_id=3, end_time=planned_end, resumed_at=None)

        work_break_service.resume(make_activity(active_break=active_break))

        self.assertEqual(active_break.end_time, planned_end)


class SessionLifecycleTests(SimpleTestCase):

    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_close_rejects_closed_session(self, repository):
        with self.assertRaises(SessionRuleError) as ctx:
            work_session_service.close(SimpleNamespace(is_closed=True))
        self.assertEqual(ctx.exception.payload, {"detail": "Session already closed"})

    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_close_closes_and_reloads(self, repository):
        session = MagicMock(is_closed=False, pk=7)

        result = work_session_service.close(session)

        session.close_session.assert_called_once_with()
        repository.get_detail.assert_called_once_with(7)
        self.assertIs(result, repository.get_detail.return_value)

    @patch(f"{SESSION_SERVICE}.force_close")
    @patch(f"{SESSION_SERVICE}.session_expires_at")
    @patch(f"{SESSION_SERVICE}.get_grace_hours", return_value=8)
    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_active_session_expired_is_force_closed(self, repository, _grace, expires_at, force_close):
        session = MagicMock()
        repository.find_open_session_of.return_value = session
        expires_at.return_value = timezone.now() - timedelta(minutes=1)

        self.assertIsNone(work_session_service.get_active_session("user"))
        force_close.assert_called_once_with(session, expires_at.return_value)

    @patch(f"{SESSION_SERVICE}.session_core_module_id", return_value=1)
    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_active_session_of_another_process_is_hidden(self, repository, _core_module):
        repository.find_open_session_of.return_value = MagicMock()
        self.assertIsNone(work_session_service.get_active_session("user", core_module_id="2"))

    @patch(f"{SESSION_SERVICE}.transaction")
    @patch(f"{SESSION_SERVICE}.force_close")
    @patch(f"{SESSION_SERVICE}.session_expires_at")
    @patch(f"{SESSION_SERVICE}.get_grace_hours", return_value=8)
    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_rotate_on_expired_session_closes_it_then_fails(
        self, repository, _grace, expires_at, force_close, _transaction,
    ):
        session = MagicMock(is_closed=False)
        repository.lock_by_id.return_value = session
        expires_at.return_value = timezone.now() - timedelta(minutes=1)
        read_input = MagicMock()

        with self.assertRaises(SessionRuleError) as ctx:
            work_session_service.rotate_activity(1, "user", read_input)

        force_close.assert_called_once_with(session, expires_at.return_value)
        read_input.assert_not_called()
        self.assertEqual(ctx.exception.payload, ["La jornada (sesión) ha expirado."])

    @patch(f"{SESSION_SERVICE}.transaction")
    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_rotate_on_closed_session(self, repository, _transaction):
        repository.lock_by_id.return_value = MagicMock(is_closed=True)

        with self.assertRaises(SessionRuleError) as ctx:
            work_session_service.rotate_activity(1, "user", MagicMock())

        self.assertEqual(ctx.exception.payload, {"detail": "La jornada (sesión) está cerrada."})

    @patch(f"{SESSION_SERVICE}.transaction")
    @patch(f"{SESSION_SERVICE}.sync_module_assignees")
    @patch(f"{SESSION_SERVICE}.validate_employee_conflicts")
    @patch(f"{SESSION_SERVICE}.validate_employees_active")
    @patch(f"{SESSION_SERVICE}.session_expires_at")
    @patch(f"{SESSION_SERVICE}.get_grace_hours", return_value=8)
    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_rotate_restarts_activity_and_syncs_assignees(
        self, repository, _grace, expires_at, validate_active, validate_conflicts, sync, _transaction,
    ):
        session = MagicMock(is_closed=False)
        repository.lock_by_id.return_value = session
        expires_at.return_value = timezone.now() + timedelta(hours=1)

        result = work_session_service.rotate_activity(1, "user", lambda: ([4, 5], [5]))

        validate_active.assert_called_once_with([4, 5])
        validate_conflicts.assert_called_once_with([4, 5], session.get_active_activity.return_value)
        session.restart_activity.assert_called_once_with(
            employee_ids=[4, 5], created_by="user", apprentice_ids=[5],
        )
        self.assertIs(result, session.restart_activity.return_value)
        sync.assert_called_once_with(result.module, "user")

    @patch(f"{SESSION_SERVICE}.transaction")
    @patch(f"{SESSION_SERVICE}.session_core_module_id", return_value=1)
    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_open_session_blocks_a_session_of_another_process(self, repository, _core_module, _transaction):
        active = MagicMock()
        active.get_active_activity.return_value.module.name = "Modulo 3"
        repository.lock_open_session_of.return_value = active
        repository.find_module_with_location.return_value = SimpleNamespace(
            location_id=1, location=SimpleNamespace(core_module_id=2),
        )
        create = MagicMock()

        with self.assertRaises(ValidationError) as ctx:
            work_session_service.open_session("user", 10, create)

        self.assertIn('"Modulo 3"', str(ctx.exception.detail[0]))
        active.close_session.assert_not_called()
        create.assert_not_called()

    @patch(f"{SESSION_SERVICE}.transaction")
    @patch(f"{SESSION_SERVICE}.session_core_module_id", return_value=1)
    @patch(f"{SESSION_SERVICE}.WorkSessionRepository")
    def test_open_session_closes_previous_session_of_same_process(self, repository, _core_module, _transaction):
        active = MagicMock()
        repository.lock_open_session_of.return_value = active
        repository.find_module_with_location.return_value = SimpleNamespace(
            location_id=1, location=SimpleNamespace(core_module_id=1),
        )
        create = MagicMock(return_value="new-session")

        self.assertEqual(work_session_service.open_session("user", 10, create), "new-session")
        active.close_session.assert_called_once_with()


class SessionRuleErrorMixinTests(SimpleTestCase):

    def test_error_is_answered_with_its_payload_and_status(self):
        response = SessionRuleErrorMixin().handle_exception(
            SessionRuleError({"detail": "x"}, status_code=404)
        )
        self.assertEqual((response.status_code, response.data), (404, {"detail": "x"}))

    def test_list_payload_is_kept(self):
        response = SessionRuleErrorMixin().handle_exception(SessionRuleError(["expirada"]))
        self.assertEqual((response.status_code, response.data), (400, ["expirada"]))
