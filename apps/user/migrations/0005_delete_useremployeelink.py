# UserEmployeeLink now lives in `people` as AuthUserEmployee (see people.0001_initial,
# which renames the table). State only: the table is not dropped here.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0004_snake_case_table_names"),
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="UserEmployeeLink"),
            ],
            database_operations=[],
        ),
    ]
