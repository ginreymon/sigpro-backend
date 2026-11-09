from django.db import migrations


class Migration(migrations.Migration):
    """Drop the stored WorkSession.total_time; it is derived from started_at/ended_at.

    Run database/indexes/ix_eficiencia_periodo.sql first: the old
    IX_worksession_startedat index INCLUDEd total_time and SQL Server refuses
    to drop an indexed/included column. See documents/ELIMINAR_COLUMNA_total_time.txt.
    """

    dependencies = [
        ("production", "0058_move_employee_local_to_people"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="worksession",
            name="total_time",
        ),
    ]
