from django.db import migrations

PRODUCTION_APP_MODULE_URL = "production"  # core.Module: "Producción"


def backfill_app_module(apps, schema_editor):
    WorkShift = apps.get_model('production', 'WorkShift')
    Module = apps.get_model('core', 'Module')
    production_module = Module.objects.filter(url=PRODUCTION_APP_MODULE_URL).first()
    if production_module is None:
        raise RuntimeError(
            f"No existe core.Module con url='{PRODUCTION_APP_MODULE_URL}'. "
            "Crea ese registro de menú antes de aplicar esta migración."
        )
    WorkShift.objects.filter(app_module__isnull=True).update(app_module_id=production_module.id)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0030_workshift_app_module'),
    ]

    operations = [
        migrations.RunPython(backfill_app_module, noop_reverse),
    ]
