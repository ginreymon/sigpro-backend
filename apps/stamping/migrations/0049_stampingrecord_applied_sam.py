from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def backfill_applied_sam(apps, schema_editor):
    """Copy the current master SAM into existing records that have no snapshot yet."""
    StampingRecord = apps.get_model('stamping', 'StampingRecord')
    StampingReferenceSam = apps.get_model('stamping', 'StampingReferenceSam')
    StampingRecord.objects.filter(applied_sam__isnull=True).update(
        applied_sam=Subquery(
            StampingReferenceSam.objects.filter(pk=OuterRef('stamping_reference_sam_id')).values('sam')[:1]
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0048_alter_stampingrecord_work_session_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingrecord',
            name='applied_sam',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
        ),
        migrations.RunPython(backfill_applied_sam, migrations.RunPython.noop),
    ]
