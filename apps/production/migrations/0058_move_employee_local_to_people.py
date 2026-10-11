# EmployeeLocal now lives in `people` (see people.0001_initial). The table
# production_employee_local is NOT touched: the foreign keys keep pointing to the
# same table, so this is a state-only change.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("people", "0001_initial"),
        ("production", "0057_alter_productionrecord_work_session_activity"),
        ("user", "0005_delete_useremployeelink"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="moduleassignee",
                    name="employee",
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="people.employeelocal"),
                ),
                migrations.AlterField(
                    model_name="worksessionactivityemployee",
                    name="employee",
                    field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="people.employeelocal"),
                ),
                migrations.AlterField(
                    model_name="employeecontinuousworklimit",
                    name="employee",
                    field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="continuous_work_limit", to="people.employeelocal"),
                ),
                migrations.DeleteModel(name="EmployeeLocal"),
            ],
            database_operations=[],
        ),
    ]
