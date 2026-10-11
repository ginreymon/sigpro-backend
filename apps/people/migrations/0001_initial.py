# Moves EmployeeLocal (production) and UserEmployeeLink (user) into the new `people`
# app. Data is preserved:
#   - production_employee_local keeps its name: state-only move (no SQL), so the
#     SPs and the Siesa sync that read it are not affected.
#   - user_employee_link is renamed to auth_user_employee (sp_rename, data kept)
#     and the model becomes AuthUserEmployee.
#   - content types / permissions of the moved models are re-pointed so existing
#     group permissions keep working.

import core.models.audit_model
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

OLD_TABLE = "user_employee_link"
NEW_TABLE = "auth_user_employee"

RENAME_TABLE_SQL = f"""
IF OBJECT_ID('dbo.{OLD_TABLE}', 'U') IS NOT NULL AND OBJECT_ID('dbo.{NEW_TABLE}', 'U') IS NULL
    EXEC sp_rename 'dbo.{OLD_TABLE}', '{NEW_TABLE}';
"""

REVERSE_RENAME_TABLE_SQL = f"""
IF OBJECT_ID('dbo.{NEW_TABLE}', 'U') IS NOT NULL AND OBJECT_ID('dbo.{OLD_TABLE}', 'U') IS NULL
    EXEC sp_rename 'dbo.{NEW_TABLE}', '{OLD_TABLE}';
"""

# (old app_label, old model) -> (new app_label, new model)
MOVED_CONTENT_TYPES = (
    (("production", "employeelocal"), ("people", "employeelocal")),
    (("user", "useremployeelink"), ("people", "authuseremployee")),
)


def _repoint_content_types(apps, moves):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")

    for (old_app, old_model), (new_app, new_model) in moves:
        old = ContentType.objects.filter(app_label=old_app, model=old_model).first()
        if old is None:
            continue  # fresh database: content types are created at post_migrate
        if ContentType.objects.filter(app_label=new_app, model=new_model).exists():
            continue  # already created; leave both untouched

        old.app_label = new_app
        old.model = new_model
        old.save(update_fields=["app_label", "model"])

        if old_model != new_model:
            for permission in Permission.objects.filter(content_type=old):
                action = permission.codename.split("_", 1)[0]
                permission.codename = f"{action}_{new_model}"
                permission.save(update_fields=["codename"])


def forwards(apps, schema_editor):
    _repoint_content_types(apps, MOVED_CONTENT_TYPES)


def backwards(apps, schema_editor):
    _repoint_content_types(apps, [(new, old) for old, new in MOVED_CONTENT_TYPES])


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
        ("production", "0057_alter_productionrecord_work_session_activity"),
        ("user", "0004_snake_case_table_names"),
    ]

    operations = [
        # EmployeeLocal: state only, the table already exists as production_employee_local.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="EmployeeLocal",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("is_active", models.BooleanField(default=True)),
                        ("rowid", models.BigIntegerField(unique=True)),
                        ("is_deleted", models.BooleanField(default=False)),
                        ("deleted_at", models.DateTimeField(blank=True, null=True)),
                        ("first_name", models.CharField(max_length=255)),
                        ("last_name1", models.CharField(max_length=255)),
                        ("last_name2", models.CharField(blank=True, max_length=255, null=True)),
                        ("id_number", models.CharField(max_length=50, unique=True)),
                        ("company_name", models.CharField(blank=True, max_length=255, null=True)),
                        ("contract_status", models.CharField(blank=True, max_length=50, null=True)),
                        ("cost_center_rowid", models.IntegerField(blank=True, null=True)),
                        ("cost_center_description", models.CharField(blank=True, max_length=255, null=True)),
                        ("cost_group_id", models.CharField(blank=True, max_length=50, null=True)),
                        ("cost_group_description", models.CharField(blank=True, max_length=255, null=True)),
                    ],
                    options={
                        "db_table": "production_employee_local",
                        "ordering": ["rowid"],
                    },
                    bases=(core.models.audit_model.SpanishUniqueErrorMixin, models.Model),
                ),
            ],
            database_operations=[],
        ),
        # AuthUserEmployee: the user_employee_link table is renamed, data is kept.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="AuthUserEmployee",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("auth_user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="employee_link", to=settings.AUTH_USER_MODEL)),
                        ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created", to=settings.AUTH_USER_MODEL)),
                        ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated", to=settings.AUTH_USER_MODEL)),
                        ("employee_local", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="user_link", to="people.employeelocal")),
                    ],
                    options={
                        "db_table": NEW_TABLE,
                    },
                    bases=(core.models.audit_model.SpanishUniqueErrorMixin, models.Model),
                ),
            ],
            database_operations=[
                migrations.RunSQL(RENAME_TABLE_SQL, reverse_sql=REVERSE_RENAME_TABLE_SQL),
            ],
        ),
        migrations.RunPython(forwards, backwards),
    ]
