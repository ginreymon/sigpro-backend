from django.db import migrations

AREA_NAMES = ["Confección", "Estampación", "Corte"]


def seed_and_backfill(apps, schema_editor):
    ProductionArea = apps.get_model('production', 'ProductionArea')
    Module = apps.get_model('production', 'Module')

    areas_by_name = {}
    for name in AREA_NAMES:
        area, _ = ProductionArea.objects.get_or_create(name=name)
        areas_by_name[name.strip().lower()] = area

    for module in Module.objects.exclude(location_legacy__isnull=True).exclude(location_legacy=""):
        area = areas_by_name.get(module.location_legacy.strip().lower())
        if area is not None:
            module.location = area
            module.save(update_fields=["location"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0034_add_location_fk_to_module_and_workshift'),
    ]

    operations = [
        migrations.RunPython(seed_and_backfill, noop_reverse),
    ]
