from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def backfill_applied_sam(apps, schema_editor):
    """Copy the current master SAM (sku -> rowid_item -> reference SAM) into existing records without a snapshot."""
    ProductionRecord = apps.get_model('production', 'ProductionRecord')
    SkuItemLocal = apps.get_model('production', 'SkuItemLocal')
    ReferenceSam = apps.get_model('production', 'ReferenceSam')

    # Nested OuterRef: it is resolved against ProductionRecord, two query levels up.
    rowid_item = SkuItemLocal.objects.filter(rowid=OuterRef(OuterRef('sku_rowid'))).values('rowid_item')[:1]
    ProductionRecord.objects.filter(applied_sam__isnull=True).update(
        applied_sam=Subquery(
            ReferenceSam.objects.filter(rowid_item=Subquery(rowid_item)).values('sam')[:1]
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0059_remove_worksession_total_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='productionrecord',
            name='applied_sam',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
        ),
        migrations.RunPython(backfill_applied_sam, migrations.RunPython.noop),
    ]
