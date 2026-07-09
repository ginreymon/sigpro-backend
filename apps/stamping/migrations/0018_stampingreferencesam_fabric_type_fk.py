import django.db.models.deletion
from django.db import migrations, models


def migrate_fabric_type_data(apps, schema_editor):
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")
    StampingFabricType = apps.get_model("stamping", "StampingFabricType")

    for reference_sam in StampingReferenceSam.objects.all():
        if not reference_sam.fabric_type:
            continue
        fabric_type = StampingFabricType.objects.get(name=reference_sam.fabric_type)
        reference_sam.fabric_type_new_id = fabric_type.id
        reference_sam.save(update_fields=["fabric_type_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0017_stampingreferencesam_stamp_type_description_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingreferencesam',
            name='fabric_type_new',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingfabrictype',
            ),
        ),
        migrations.RunPython(migrate_fabric_type_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='stampingreferencesam',
            name='fabric_type',
        ),
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='fabric_type_new',
            new_name='fabric_type',
        ),
    ]
