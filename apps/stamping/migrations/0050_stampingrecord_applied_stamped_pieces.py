from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def backfill_applied_stamped_pieces(apps, schema_editor):
    """Copy the current master stamped_pieces into existing records without a snapshot."""
    StampingRecord = apps.get_model('stamping', 'StampingRecord')
    StampingReferenceSam = apps.get_model('stamping', 'StampingReferenceSam')
    StampingRecord.objects.filter(applied_stamped_pieces__isnull=True).update(
        applied_stamped_pieces=Subquery(
            StampingReferenceSam.objects.filter(pk=OuterRef('stamping_reference_sam_id')).values('stamped_pieces')[:1]
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0049_stampingrecord_applied_sam'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingrecord',
            name='applied_stamped_pieces',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_applied_stamped_pieces, migrations.RunPython.noop),
    ]
