# Backend improvement plan (responsibility separation + endpoints)

Review date: 2026-10-10. Static read of `apps/*`, `core/`, `config/`. Nothing was run.
Builds on `ARCHITECTURE_ROADMAP.md` (still valid, except `apps/catalog` which no longer exists). This file re-verifies it against the current code and adds new findings.

Target: View -> Service -> Repository -> DB/SP. Serializers validate/transform. Models hold data and constraints.

---

## 1. Verdict: is it well separated?

| Area | State | Evidence |
|---|---|---|
| Stored-procedure reads (productivity, OP detail, trazabilidad) | **Good** | `BaseProductivityRepository` / `BaseProductivityService` / `BaseProductivityViewSet` shared by production and stamping; `exec_json_procedure` for JSON SPs; views only parse params and call the service |
| CRUD of simple catalogs | **Acceptable** | thin ViewSets over `AuditModelViewSet` / `LocalBaseModelViewSet` |
| Work sessions / activities / breaks | **Poor** | pause/resume/rotate/close rules, `select_for_update`, message building and ORM queries live in `work_session_view.py` and `work_session_activity_view.py`; no repository |
| Serializers with orchestration | **Poor** | `WorkSessionSerializer.create/update` creates snapshots, activities, employees and syncs assignees (should be a service) |
| Audit records (stamping) | **Mixed** | 6 ORM usages in `audit_record_view.py` (confirm, status, audited-ops, bulk delete) |
| Authorization | **Missing** | see 2.1 |
| Cross-app dependencies | **Poor** | `common` -> `production` via lazy imports (`op_record_batch_service`), `user` -> `production` (`EmployeeLocal`), `integration` <-> production/stamping |
| Tests | **Missing** | only `integration/tests.py` (130 lines); every other `tests.py` is the Django stub |

---

## 2. Findings

### 2.1 Critical
1. **No server-side access control.** Only `IsAuthenticated` (global default). `Option`/`GroupOption` permissions are checked only by the frontend (`accessGuard`) and the `has-access` endpoint. Any logged-in user can call any endpoint (create users, edit groups, close other people's sessions, read efficiency).
2. **`password-reset-request` is `AllowAny` and returns `reset_token` in the response** (`auth_view.py`). Username + id_number is enough to take over an account. `password-reset-confirm` skips `AUTH_PASSWORD_VALIDATORS`.
3. **No throttling** (login, reset, refresh) — nothing under `DEFAULT_THROTTLE_*`.
4. `password-reset-request` returns 200 "Datos inválidos" for unknown employee, but an uncaught `UserEmployeeLink.DoesNotExist` gives 500: leaks which employees have accounts.
5. Swagger/ReDoc exposed without auth in `config/urls.py`.

### 2.2 High (structure)
1. `work_session_view.py` / `work_session_activity_view.py` hold business logic (see table). Two different "close session" paths: `close_session()` (model) vs `finalize_expired_session()` (service).
2. `WorkSessionSerializer` does orchestration; also imports `WorkBreakRecordSerializer` inside a method (circular import smell).
3. `common/services/op_record_batch_service.py` imports production models/repositories lazily and builds `ModuleDowntime` — domain logic of production inside `common`.
4. `StampingRecordViewSet._additional_times_extra_seconds` does ORM + math in the view module.
5. `ProductivityViewSet.efficiency_report` and `efficiency_report_export` duplicate the same param parsing (+ `parse_optional_int` swallows invalid ints silently, returning `None` instead of 400).
6. `get_module_shift_summary` / `get_module_efficiency` filter in Python after the SP returns everything (SP could take `@ModuleType`).

### 2.3 Medium (endpoints / API contract)
1. **Error shape inconsistent**: `{"error": ...}`, `{"detail": ...}`, `{"message": ...}`, bare list (`Response(["La jornada ... expirado."], 400)`), DRF `ValidationError`. Frontend must handle all.
2. **Validation in views by hand**: `_handle_pause` has ~7 `if ... return Response(400)`; should be an input serializer (like `ContinueInputSerializer` already in `work_session_view.py`).
3. **Query-param parsing repeated**: `missing = [...] ; raise ValidationError` appears 3x in `audit_record_view.py`. Needs one input serializer / helper.
4. **Inconsistent verbs/paths**: `rotate` action named `rotate_activity`; `status_for_op` uses camelCase params (`docType`, `docNumber`) while the rest use snake_case; `bulk` mixes PUT+DELETE in one action; `pause` vs `pause-autoresume`.
5. **Same URL name in two apps**: `production-orders` in `/production/` and `/stamping/`.
6. **Empty-prefix routers** (`r""`) in `core` and `integration` shadow future routes.
7. `BaseModelViewSet.filterset_fields = "__all__"` + `ordering_fields = "__all__"` exposes every column (incl. FKs to user) for filtering/ordering on all CRUD endpoints. Index/perf and information exposure risk.
8. `LocalBaseModelViewSet.update` ignores everything except `editable_fields` silently (PUT returns 200 without saving other fields).
9. `except Exception: return []/{}` in `op_production_detail_serializer` hides malformed SP JSON.
10. Pagination: LimitOffset with no `max_limit`; `/all/` action has `pagination_class=None` on every model (unbounded).
11. N+1 risk: `WorkSessionSerializer` walks `work_session_activities` several times (prefetch exists, but `_get_active_activity` re-evaluates per call).

### 2.4 Low
- Dead/shadowed files: `production/models.py`, `production/views.py`, `user/models.py`, `user/views.py`, `core/models.py`, stub `tests.py`/`admin.py`, `db.sqlite3`, stale `__pycache__`.
- `production/{exports,reports,helpers}` are three tiny folders for one feature.
- Mixed Spanish/English naming in repositories (`get_detalle_*`, `get_tiempos_operacion_modulo`) and URL `referencias`.
- Settings: hardcoded `localhost:4200` CORS, `TrustServerCertificate=yes`, no secure-cookie/HSTS flags, import-time `mkdir`, global `Field.default_error_messages` monkey patch, loggers missing for `stamping`/`user`/`common`/`core`.

---

## 3. Plan (ordered by risk/benefit, each step = its own commit)

| # | Step | Files | Risk | Benefit |
|---|---|---|---|---|
| 1 | **Server-side permissions**: `OptionPermission` DRF class using `Option`/`GroupOption`; per-ViewSet `required_option` (config, not code); start in log-only mode, then enforce | `core/permissions.py`, ViewSets | Med (can lock users out) — roll out per module | Closes 2.1.1 |
| 2 | **Auth hardening**: stop returning `reset_token` (deliver out of band), run password validators on confirm, uniform response for unknown user, catch `UserEmployeeLink.DoesNotExist` | `auth_view.py` (+ `AuthService`) | Med (frontend flow changes) | 2.1.2 / 2.1.4 |
| 3 | **Throttling**: `ScopedRateThrottle` on login/refresh/reset; protect Swagger behind auth | `settings.py`, `urls.py` | Low | 2.1.3 / 2.1.5 |
| 4 | **Error contract**: one DRF `EXCEPTION_HANDLER` normalising to `{detail, code, errors}`; replace bare-list/`error`/`message` responses | `core/exceptions.py`, views | Med (frontend parsing) — do together with a frontend change | 2.3.1 |
| 5 | **Input serializers for params**: `PeriodQuerySerializer`, `OpQuerySerializer`, `PauseInputSerializer`; remove hand-written 400s and make invalid ints a 400 | `common/views/productivity_params.py`, `audit_record_view.py`, `work_session_activity_view.py` | Low | 2.2.5 / 2.3.2 / 2.3.3 |
| 6 | **`WorkSessionService` + `WorkBreakService`**: move pause/resume/rotate/close/create-guard out of views; unify `close_session`/`finalize_expired_session`; serializer `create/update` calls the service | `production/services/`, `work_session_*_view.py`, `work_session_serializer.py` | **High** (core flow) — needs characterization tests first | 2.2.1 / 2.2.2 |
| 7 | **Break `common -> production` cycle**: move `op_record_batch_service` to `production/services` (or inject callables); same for `user -> production` | `common/`, `user/` | Med | 2.2.3 |
| 8 | **AuditRecordService/Repository** for `confirm`, `status`, `audited-ops`, `bulk delete` | `stamping/` | Low | 2.2 |
| 9 | **Restrict filters**: explicit `filterset_fields`/`ordering_fields` per ViewSet; `max_limit` on pagination; bound `/all/` | `base_model_view.py`, ViewSets | Med (frontend may rely on `__all__`) — grep frontend first | 2.3.7 / 2.3.10 |
| 10 | **Filter by module type in SP** instead of Python (`@ModuleType`) | `sp_*` + repositories | Med (DB change, user deploys) | 2.2.6 |
| 11 | **Cleanup**: delete shadowed stub files, `db.sqlite3`, `__pycache__`; merge `exports/reports/helpers` into one `production/reporting/`; rename `rotate_activity`, camelCase params with aliases kept for one release | misc | Low | 2.4 |
| 12 | **Tests**: characterization tests for steps 6-8 *before* touching them (session open/close/rotate/pause/resume, manual-duration-batch, audit bulk); use a SQLite-free approach (SPs need SQL Server -> mock repositories) | `apps/*/tests/` | Low | enables 6-8 safely |

Suggested order: **12 (for the parts about to change) -> 3 -> 2 -> 1 -> 5 -> 4 -> 8 -> 7 -> 6 -> 9 -> 10 -> 11.**

## 4. Not recommended (YAGNI)
- A repository layer for every simple CRUD model: plain ViewSets over `ModelViewSet` are enough; add repositories only where there are queries/rules (sessions, audit records, TEP submissions).
- Splitting `core` into several apps now: the benefit is low versus the migration/contenttype cost.

## 5. Impact per layer
| Layer | Impact |
|---|---|
| Frontend | steps 1, 2, 4, 9 change observable behavior (403s, reset flow, error shape, filters) — coordinate |
| Backend | all steps |
| Database | only step 10 (optional) |
| API | 4, 5, 9 and renames in 11 are contract changes; keep old names for one release |

Every step needs your approval before coding (project rule); steps 1, 2, 4 and 9 especially.

## 6. Progress: step 7 (app dependencies), done 2026-10-10

Done (no migrations, `manage.py check` OK, `makemigrations --check` reports no changes):
- `common` no longer imports `production` (was 8 imports, 6 lazy + 2 `apps.get_model`). `op_record_batch_service` and `OpRecordViewSet` moved to `apps/production/{services,views}/`; stamping now imports them from production (allowed direction). `BaseProductivityService` takes `module_model` from its subclasses.
- `production` no longer imports `stamping` for traceability: `get_trazabilidad_op_json` moved to `apps/common/repositories/op_common_repository.py` (its SP lives in `database/sp/common`).

Also done (same day):
- `production -> stamping` removed: `ModuleSerializer` no longer imports stamping. It exposes `module_extensions` (`production/serializers/module_extensions.py`); stamping registers `ModuleMachineExtension` in `StampingConfig.ready()` (`stamping/serializers/module_machine_extension.py`), which owns `machine`, `machine_id`, `uses_processes_search` and the assignment sync. Same API fields as before.
- `user -> production` loosened in the model: `UserEmployeeLink.employee_local` uses the string FK `"production.EmployeeLocal"` (no migration change). Views/serializers of `user` still use `EmployeeLocal` (one-way dependency, no cycle).

- `OpRecord` moved to `apps/common/models/op_record.py` (abstract model, no table: `makemigrations --check` reports no changes). `production`/`stamping` no longer import `integration`.

- `integration` no longer imports `production`/`stamping`: `WorkCenterProductionArea` uses string FKs; `tep_submission_service` resolves its record models (`RECORD_MODELS = {1: "production.ProductionRecord", 2: "stamping.StampingRecord"}`) through the app registry (`record_model()`).
- `user` no longer imports `production`: every reference goes through `apps/user/employee.py` (`get_employee_model()`, `get_employee_serializer_class()`).

Resulting graph: static imports go only `stamping -> production -> common` (and `stamping -> common`). `integration` and `user` have no static imports of production/stamping. The functional dependency still exists by design (TEP submission needs the record tables; accounts link to employees) but is declared in one place per app and resolved at runtime. `manage.py check` OK, `makemigrations --check` no changes, `manage.py test apps.integration` 13/13 OK.

## 7. Progress: `people` app (employee + account link), 2026-10-11

- New app `apps/people` owns `EmployeeLocal` (table `production_employee_local`, unchanged) and `AuthUserEmployee` (was `user.UserEmployeeLink`; table `user_employee_link` -> `auth_user_employee`). `EmployeeLocalSerializer` moved with them.
- Migrations: `people.0001_initial` (state-only for EmployeeLocal, `sp_rename` for the link table, content types/permissions re-pointed), `user.0005_delete_useremployeelink` and `production.0058_move_employee_local_to_people` (both state-only). Verified: `makemigrations --check` clean; migration graph builds and project state resolves the new models and FKs. NOT applied to any database.
- `apps/user/employee.py` (the get_model/import_string layer) was removed: `user` and `production` import `apps.people` directly (downward arrow, `people` imports nothing from them).
- API contract unchanged (routes `/production/employees/`, `/user/employee-directory/`, field `employee_local_id`). `EmployeeLocalViewSet` stays in `production` because it filters by `ProductionAreaCostCenter`.
- Graph: `people` <- `production` <- `stamping`; `user` -> `people`.

## 8. Progress: sessions / activities / breaks (step 6), 2026-10-11

- Rules moved out of `work_session_view.py` and `work_session_activity_view.py`:
  - `services/work_session_service.py`: `open_session`, `close`, `get_active_session`, `rotate_activity` (next to the existing expiry helpers).
  - `services/work_break_service.py`: `pause` (incl. auto-resume) and `resume`.
  - `repositories/work_session_repository.py`: `WorkSessionRepository` (detail queryset, `select_for_update` locks) and `WorkSessionActivityRepository`.
  - `services/exceptions.py` + `views/session_rule_error_mixin.py`: `SessionRuleError(payload, status_code)` keeps every response exactly as before (`{"detail": ...}`, the bare-list "expirada" payload, the 404 for an unknown break type).
- Behaviour kept on purpose: validation order of `pause`; an expired session is force-closed and that close is committed (the error is raised after the transaction ends); `rotate` validates its body only after the session checks.
- Views no longer use `.objects`, `select_for_update`, `transaction` or `timezone` (only the class-level `queryset` the router needs).
- Not done (out of scope here): `WorkSessionSerializer.create/update` orchestration and the model methods `close_session` / `WorkSessionActivity.close` vs `finalize_expired_session` (two close paths still exist). Unit tests with mocked repositories (26 new); nothing was run against SQL Server.

## 9. Progress: WorkSessionSerializer orchestration, 2026-10-11

- `WorkSessionSerializer` now only validates and represents; `create`/`update` delegate to `services/work_session_setup_service.py` (`create_session`, `update_session`, `snapshot_shift`, `assign_employees`), which owns the transactions and the checks (module conflict, active employees, employee conflicts, "no employees without a module", "no active activity").
- ORM access moved to `WorkSessionRepository` (create/update, shift snapshot, employee snapshots). `ModelSerializer.create/update` were replaced by the equivalent `objects.create(**data)` / set attributes + `save()`.
- 8 unit tests added (mocked repository); 54 production/stamping/integration tests pass. Nothing was run against SQL Server.
- Still open: two close paths (`WorkSession.close_session` / `WorkSessionActivity.close` vs `finalize_expired_session`); `get_active_activity` still imports `WorkBreakRecordSerializer` inside the method.

### Decision on the two close paths (2026-10-11)
`WorkSession.close_session` and `work_session_service.finalize_expired_session` are **kept as they are, on purpose**; they are not unified. They differ: manual close ends the session at `now` and does not set `editing_finalized`; the expiry close ends it at `max(expires_at, started_at)`, sets `editing_finalized` and runs in its own transaction. Both close the active activity with `activity.close()` (uses `now`). The tests in `SessionCloseTests` pin that behaviour. Any future change to it (e.g. closing the activity at `expires_at`) must be a deliberate decision because it changes the `end_time` values used by the efficiency calculation.

## 10. Standard error envelope (step 4), 2026-10-11

Every 4xx/5xx JSON response under `/api/v1/` now has:

```json
{ "detail": "message (first error)", "code": "validation_error", "errors": { "field": ["message"] } }
```

- `errors` is `{}` when there are no field errors; non-field messages go in `errors.non_field_errors`.
- `code`: `validation_error`, `not_authenticated`, `permission_denied`, `not_found`, `method_not_allowed`, `throttled`, `business_rule` (session/break rules), `bad_request`, `server_error`... (SimpleJWT keeps its own, e.g. `token_not_valid`).
- Produced by `core/exceptions.py`: `api_exception_handler` (REST_FRAMEWORK `EXCEPTION_HANDLER`: everything DRF handles), `ApiErrorEnvelopeMiddleware` (manual `Response(..., status=4xx)` written before the standard) and `api_not_found` / `api_server_error` (JSON 404/500 only for `/api/`). `error_response(detail, status_code=, code=)` is the helper for new manual errors. Success responses are never touched.
- **Legacy mirror** (`API_ERRORS_LEGACY_MIRROR`, default `False`): roll-back switch. When `True`, the keys of the previous shapes (`error`, `message`, form field names, TEP `details`) are also copied next to the envelope. A field called `code`/`errors`/`detail` is only read from `errors` (never mirrored at the top level, to avoid clashing with the envelope).
- Shape changes that cannot be mirrored: a body that used to be a **list** (e.g. `["La jornada (sesión) ha expirado."]`) is now the envelope with `errors.non_field_errors`.

Frontend: `common/functions/api-error.ts` (`apiErrorDetail`, `apiErrorCode`, `apiFieldErrors`, `apiNonFieldErrors`) reads the envelope first and falls back to the old shapes, so it works against old and new backends. Migrated readers: `session-errors.ts`, `base-crud-page.ts` (`markServerFieldErrors`), `actions-crud-page.ts`, `pause-modal.ts`, `shift-cycles.ts`.

**Deployment order (important):** deploy the frontend first, then the backend. Deploying the backend first would break old frontends in two places: forms with a field called `code` (the old reader would take the envelope `code` as that field's error) and bodies that used to be lists.

### Status after the full pass

- Every manual error `Response` in `apps/` (auth, productivity, integration/TEP, audit, order lookups, role delete, shared `common/http.py`) now uses `error_response(detail, status_code=, code=, errors=, legacy=, extra=)` or raises (serializer errors go through the exception handler). No manual `Response({"error": ...}, status=4xx/5xx)` is left. The middleware stays as a safety net for anything new that forgets it.
- `error_response` codes: `missing_params`, `invalid_params`, `invalid_param`, `missing_credentials`, `invalid_credentials`, `missing_refresh_token`, `invalid_refresh_token`, `wrong_password`, `same_password`, `token_expired`, `invalid_token`, `role_has_users`, `audit_block_not_found`, `not_found`, `invalid_tep_request`, `invalid_tep_document`, `invalid_register_ids`, `siesa_not_configured`, `siesa_unreachable`, `siesa_rejected`.
- Domain data that travels with an error is kept through `extra`: a rejected TEP answers 422 with the envelope **and** `submission_id`, `ok`, `error_type`, `error_detail_xml`. `register_ids` problems are in `errors.register_ids`.
- Frontend: all readers go through `common/functions/api-error.ts` (`manual-integration.ts` included). Login / confirm-password show fixed texts and do not read the body; `forgot-password` reads a 200 success body, not an error. No Playwright test asserts an error shape.
- Tests: backend 85 (core 25), frontend 11 for `api-error`. Not run against SQL Server or in a browser.

### Legacy mirror: off by default

`API_ERRORS_LEGACY_MIRROR` now defaults to `False`: the only top-level keys of an error are `detail`, `code`, `errors` (+ `extra` data such as the TEP result). Every frontend reader already reads the envelope, so nothing in the app depends on the old keys. The switch stays only as a roll-back for a bad rollout (a browser with a cached old frontend keeps reading `error` / `message` / form field keys: set `API_ERRORS_LEGACY_MIRROR=True` in the environment, no code change). Once the new frontend is the only one in use, the `legacy=` arguments in `error_response` calls and the mirror code can be deleted.

Known leftovers: `password-reset-request` answers 200 with `{"message": "Datos inválidos"}` (a 200, so it is not an error for the envelope; fixed with the auth hardening step).