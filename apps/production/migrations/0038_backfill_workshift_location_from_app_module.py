from django.db import migrations


def backfill_location(apps, schema_editor):
    WorkShift = apps.get_model('production', 'WorkShift')
    ProductionArea = apps.get_model('production', 'ProductionArea')

    areas_by_core_module = {
        area.core_module_id: area
        for area in ProductionArea.objects.exclude(core_module_id__isnull=True)
    }

    for shift in WorkShift.objects.filter(location__isnull=True, app_module__isnull=False):
        area = areas_by_core_module.get(shift.app_module_id)
        if area is not None:
            shift.location = area
            shift.save(update_fields=["location"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0037_rename_production_area_core_module'),
    ]

    operations = [
        migrations.RunPython(backfill_location, noop_reverse),
    ]
