from django.db import migrations, models
from django.db.models import F, Value
from django.db.models.functions import Coalesce


def fill_missing_names(apps, schema_editor):
    """`name` becomes required: rows without one take their custom_reason, or a generic text."""
    ModuleDowntime = apps.get_model('production', 'ModuleDowntime')
    ModuleDowntime.objects.filter(name__isnull=True).update(
        name=Coalesce(F('custom_reason'), Value('PARO SIN MOTIVO'))
    )


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0061_remove_module_downtime_work_break_and_resumed_at'),
    ]

    operations = [
        migrations.RunPython(fill_missing_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='moduledowntime',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.RemoveField(
            model_name='moduledowntime',
            name='custom_reason',
        ),
    ]
