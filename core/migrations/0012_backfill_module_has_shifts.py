from django.db import migrations

PRODUCTION_APP_MODULE_URL = "production"  # core.Module: "Producción"


def backfill_has_shifts(apps, schema_editor):
    Module = apps.get_model('core', 'Module')
    Module.objects.filter(url=PRODUCTION_APP_MODULE_URL).update(has_shifts=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_module_has_shifts'),
    ]

    operations = [
        migrations.RunPython(backfill_has_shifts, noop_reverse),
    ]
