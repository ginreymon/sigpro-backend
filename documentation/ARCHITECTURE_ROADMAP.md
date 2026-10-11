# Backend Architecture Roadmap

Source: static audit of `apps/production`, `apps/stamping`, `apps/catalog`, `apps/integration`, `apps/user`, `apps/common`, `core/`, `config/`. No code was run; every finding comes from reading the code. Line numbers are approximate.

Target architecture: **View -> Service -> Repository -> DB/SP**. Serializers only validate/transform. Models hold data and constraints only.

---

## 1. Target layer responsibilities

| Layer | Owns | Must NOT |
|---|---|---|
| View | parse request, call service, serialize response, permissions | ORM, transactions, business rules, inline param validation |
| Serializer | field validation, representation | `create`/`update` orchestration, repository calls, queries |
| Service | business rules, transactions, orchestration | raw SQL/ORM (go through repository) |
| Repository | ORM queries and `EXEC sp_*`, returns dicts/rows | business rules |
| Model | fields, constraints, trivial properties | orchestration, cross-app side effects, `save()` magic |

## 2. App dependency rules

- `core` imports nothing from `apps.*`.
- `common` imports only `core`. Never production/stamping/integration (replace lazy imports with injected callables or abstract bases).
- `user` imports `core` + access models. References `EmployeeLocal` via string FK or a public service, not production serializers/views.
- `production`, `stamping`, `catalog` import `core`, `common`. Avoid importing each other's internals; stamping -> production only through public services.
- `integration` is the top of the graph; nothing imports it (so `OpRecord` must leave it).
- Cross-app imports only of another app's `models`/`services`, never `views`/`serializers`/`repositories`. Enforce with import-linter in CI.

## 3. Findings summary

### Critical (security)
1. `apps/user/views/auth_view.py` `password-reset-request` (AllowAny) returns `reset_token` in the response; username + employee id_number is enough to take over an account.
2. `password_reset_confirm` skips `AUTH_PASSWORD_VALIDATORS`, only catches `DoesNotExist`, no rate limit.
3. Invalid reset returns 200 "Datos inválidos"; uncaught `UserEmployeeLink.DoesNotExist` -> 500 leaks which employees have accounts.
4. No DRF throttling configured (login + reset unthrottled). Swagger/ReDoc exposed unauthenticated.

### High (structure)
- **Cycles:** integration <-> production/stamping (`OpRecord` in integration, FK back); `common` -> `production` hidden via lazy imports (`op_record_batch_service`); `user` -> production internals; stamping <-> production.
- **Business logic in views:** `work_session_activity_view`, `work_session_view`, `sku_item_local_view`, `reference_sam_view`, `productivity_view`, stamping `audit_record_view`, `stamping_record_view`, catalog `technical_sheet_view`, `auth_view`, `core/views/menu_view`.
- **Business logic in serializers:** production `module`, `work_session`, `production_record`, `production_area`; stamping `stamping_record`, `audit_record`; user `group`, `register`, `user_update`.
- **Business logic in models:** `WorkSession.start_activity/close_session`, `WorkSessionActivity.close` (cross-app), `ModuleDowntime.save`. Session close exists twice with different semantics (`close_session` vs `finalize_expired_session`).
- **Missing repositories:** production sessions/modules/employees/records/SKU-SAM, stamping records/audit, integration `TepSubmission`, user, catalog (not on shared SP helper).
- **Base classes misplaced:** `LocalBaseModelViewSet` lives in `production/views` but is used by catalog; three view bases in play (`BaseModelViewSet`, `LocalBaseModelViewSet`, `AuditModelViewSet`) with inconsistent usage.
- **Uncommitted refactor:** `apps/common/*productivity*` files are untracked but imported by production/stamping; a clean checkout breaks until committed.

### Medium
- SP helper inconsistency: `sp_json.exec_json_procedure`, `productivity_repository.rows_with_json`, `op_totals_repository`, catalog `technical_sheet_repository` each re-implement cursor/JSON handling.
- Timezone duplication: `COLOMBIA_TZ` vs hardcoded `timedelta(hours=-5)` in `helpers/excel_formatters.py`; `shift_start_utc` imported from production by common.
- Duplicated query/logic: SAM subquery x3, `efficiency_report` vs export param parsing, `list()` pagination pattern (stamping reference SAM, technical sheet), pending-quantity checks duplicated in serializers, N+1 in `technical_sheet_serializer` fallback.
- Unvalidated `int()` casts on query params cause 500s (several views); status codes 404 used for empty results; error keys `error` vs `detail` mixed.
- `siesa_webservice_client.py` mixes config, XML, transport, parsing; broad `except Exception -> None` in `tep_submission_service`.
- `settings.py`: middleware order, hardcoded CORS/DB driver/`TrustServerCertificate=yes`, no secure-cookie/HSTS settings, global `Field.default_error_messages` monkey-patch, import-time `mkdir`, missing loggers for stamping/catalog/user/common/core.
- `core` holds domain models (Module, Option, GroupOption, AppSetting, HomeView) -> acting as a mini-app.
- Stamping `scripts/` (one-off Excel importers with raw SQL, input files not tracked) should be management commands + service.

### Low
- Dead/shadowed files: `production/{models,views,tests}.py`, `user/{models,views}.py`, `core/{models,views}.py`, stamping `admin.py` stub, unused `PRODUCTION_COST_CENTERS`, stale `__pycache__` for removed modules, `db.sqlite3`, BOM in `collection_view.py`.
- Naming: mixed Spanish/English (`get_detalle_*`, `referencias/`), redundant `stamping_` file prefix, `stamping-records` without basename, URL `production-orders` in both production and stamping, empty-prefix router registrations (`r""`) in core/integration/user.
- `production/{exports,reports,helpers}` = three tiny dirs for one feature.
- Tests: effectively none outside integration builders (13 tests). All other `tests.py` are Django stubs.

## 4. Roadmap (ordered; each phase = small, separately reviewable commits)

Per project rules, each phase needs approval before code; DB/API/shared-base changes need explicit confirmation.

### Phase 0 — Hygiene, zero behavior change (low risk)
- Commit the `apps/common/*productivity*` refactor with its modified production/stamping files (one commit).
- Delete dead stubs (`production/{models,views,tests}.py`, `user/{models,views}.py`, `core/{models,views}.py`), `db.sqlite3`, dead constant; add `graphify-out/`, `.claude/` to `.gitignore` if appropriate.
- Fix BOM, in-function imports, admin gaps.

### Phase 1 — Security (do before growth)
- Remove `reset_token` from response; deliver out of band (email) or drop the flow; generic response for unknown user/employee.
- Run `validate_password` in reset confirm; catch all lookup errors.
- Add DRF throttles (login, reset). Gate Swagger/ReDoc behind DEBUG/IsAdminUser.
- Settings hardening: middleware order, secure cookies/HSTS, env-driven CORS/DB options, loggers for all apps.

### Phase 2 — Shared kernel in `core` (unblocks everything)
- Move `LocalBaseModelViewSet` to `core/views`; keep a re-export shim in production until imports are updated.
- Single SP helper in `core/repositories`: `exec_json_procedure`, `exec_rows_procedure`, `exec_row_procedure` (dict rows via `cursor.description`); migrate `sp_json`, `productivity_repository`, `op_totals_repository`, catalog repository onto it.
- Move generic utils to `core/utils`: `translate_keys`, timezone/shift helpers (`COLOMBIA_TZ`, `shift_start_utc`, `session_expires_at`), Decimal helper, Excel formatters.
- Common view helpers: query-param serializer pattern (fixes `int()` 500s), pagination/list mixin, one error-response shape (`detail`).

### Phase 3 — Break the dependency cycles
- Move `OpRecord` (+ `OpWorkRecord`) ownership out of integration into `common` (**migration impact: state-only move; needs explicit confirmation + plan**).
- Remove `common -> production` lazy imports in `op_record_batch_service` via injected callables/abstract bases.
- `user` -> production: use string FK / public service for `EmployeeLocal`; stop importing production serializers.
- Add import-linter contracts encoding the rules in section 2.

### Phase 4 — Repositories + services, app by app
Order by risk/value: **production -> stamping -> user/auth -> catalog -> integration -> core/menu**.
For each app: create repositories for ORM access; move view/serializer/model orchestration into services; slim views; serializers validate only.

Production:
- `WorkBreakService` (pause/resume/auto-resume), `WorkSessionService` (start/rotate/close/expire — single close path, replaces `WorkSession.close_session` and `finalize_expired_session` divergence), `ModuleService` (next number, machine/user sync), `ProductionRecordService` (quantity limit, activity rotation).
- `SkuItemRepository` owning the SAM subquery once; `ReferenceSamRepository`.
- Management command `close_expired_sessions` calls a service only.
- Merge `exports/reports/helpers` into one `exports/` package.

Stamping:
- `StampingRecordService` (pending-qty validation, additional-time sync, extra seconds), `AuditRecordService/Repository`, `StampingImportService` + management commands replacing `scripts/`.

User/auth: `AuthService`, `UserService`, `GroupService` + repositories.
Catalog: list assembly into `TechnicalSheetService`; fix N+1; consistent `Local*` base.
Integration: `TepSubmissionRepository`; split SIESA client into client / xml builder / response parser; remove blanket `except`.
Core: `MenuService`; consider extracting `apps/access` (Module, Option, GroupOption, HomeView, AppSetting) later.

### Phase 5 — Tests (parallel from Phase 4 onward)
Write service tests as logic moves out. Priority: auth + password reset, work-session lifecycle, pending-quantity validation, audit-record bulk replace/confirm, additional-times sync, technical-sheet list, permission checks (`has_access`). Add CI running tests + import-linter.

### Phase 6 — Naming and URL consistency
English names for services/SP wrappers, drop redundant prefixes, basenames on all routers, unique URL prefixes, replace empty-prefix routers, single `urls.py` per app. **API-changing items require explicit confirmation and frontend coordination.**

## 5. Risks
- Moving `OpRecord` touches migrations (state-only expected; confirm before generating).
- URL/API renames break the Angular frontend; defer to Phase 6 and version or alias.
- Pulling logic out of serializers/models changes call sites; each move needs tests first (Phase 5 overlaps).
- Session-close unification may change behavior; compare semantics before choosing one.

## 6. Definition of done per app
No ORM/SQL in views or serializers; every table access via a repository; services own transactions; params validated by serializers; no forbidden cross-app imports (import-linter green); service-level tests exist; English-only comments/docstrings.
