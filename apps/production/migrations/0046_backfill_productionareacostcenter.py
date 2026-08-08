from django.db import migrations


def backfill_cost_centers(apps, schema_editor):
    ProductionArea = apps.get_model('production', 'ProductionArea')
    ProductionAreaCostCenter = apps.get_model('production', 'ProductionAreaCostCenter')

    for area in ProductionArea.objects.exclude(cost_centers__isnull=True):
        rowids = area.cost_centers or []
        ProductionAreaCostCenter.objects.bulk_create([
            ProductionAreaCostCenter(production_area=area, cost_center_rowid=rowid)
            for rowid in set(rowids)
        ])


def unfill_cost_centers(apps, schema_editor):
    ProductionAreaCostCenter = apps.get_model('production', 'ProductionAreaCostCenter')
    ProductionAreaCostCenter.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0045_remove_productionarea_cost_centers_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_cost_centers, unfill_cost_centers),
    ]
