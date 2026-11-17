from django.db import migrations, models
from django.db.models import OuterRef, Subquery


def backfill_standard_time_minutes(apps, schema_editor):
    """Copy the current master standard time into the existing record selections."""
    Selection = apps.get_model('stamping', 'StampingRecordAdditionalTime')
    AdditionalStampingTime = apps.get_model('stamping', 'AdditionalStampingTime')
    Selection.objects.filter(standard_time_minutes__isnull=True).update(
        standard_time_minutes=Subquery(
            AdditionalStampingTime.objects.filter(pk=OuterRef('additional_stamping_time_id'))
            .values('standard_time_minutes')[:1]
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0050_stampingrecord_applied_stamped_pieces'),
    ]

    operations = [
        migrations.RenameField(
            model_name='additionalstampingtime',
            old_name='standard_time',
            new_name='standard_time_minutes',
        ),
        migrations.RenameField(
            model_name='additionalstampingtimestep',
            old_name='standard_time',
            new_name='standard_time_minutes',
        ),
        migrations.AddField(
            model_name='stampingrecordadditionaltime',
            name='standard_time_minutes',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True),
        ),
        migrations.RunPython(backfill_standard_time_minutes, migrations.RunPython.noop),
    ]
