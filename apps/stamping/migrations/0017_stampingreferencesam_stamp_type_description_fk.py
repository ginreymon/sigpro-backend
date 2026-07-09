import django.db.models.deletion
from django.db import migrations, models


def migrate_stamp_type_description_data(apps, schema_editor):
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")
    StampingStampTypeDescription = apps.get_model("stamping", "StampingStampTypeDescription")

    for reference_sam in StampingReferenceSam.objects.all():
        if not reference_sam.stamp_type_description:
            continue
        stamp_type_description = StampingStampTypeDescription.objects.get(name=reference_sam.stamp_type_description)
        reference_sam.stamp_type_description_new_id = stamp_type_description.id
        reference_sam.save(update_fields=["stamp_type_description_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0016_stampingreferencesam_location_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingreferencesam',
            name='stamp_type_description_new',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingstamptypedescription',
            ),
        ),
        migrations.RunPython(migrate_stamp_type_description_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='stampingreferencesam',
            name='stamp_type_description',
        ),
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='stamp_type_description_new',
            new_name='stamp_type_description',
        ),
    ]
