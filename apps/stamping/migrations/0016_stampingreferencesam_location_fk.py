import django.db.models.deletion
from django.db import migrations, models


def migrate_location_data(apps, schema_editor):
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")
    StampingLocation = apps.get_model("stamping", "StampingLocation")

    for reference_sam in StampingReferenceSam.objects.all():
        if not reference_sam.location:
            continue
        location = StampingLocation.objects.get(name=reference_sam.location)
        reference_sam.location_new_id = location.id
        reference_sam.save(update_fields=["location_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0015_stampingreferencesam_piece_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingreferencesam',
            name='location_new',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampinglocation',
            ),
        ),
        migrations.RunPython(migrate_location_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='stampingreferencesam',
            name='location',
        ),
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='location_new',
            new_name='location',
        ),
    ]
