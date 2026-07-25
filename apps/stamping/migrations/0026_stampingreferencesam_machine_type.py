import django.db.models.deletion
from django.db import migrations, models


def backfill_machine_type(apps, schema_editor):
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")

    for reference_sam in StampingReferenceSam.objects.select_related("machine").all():
        reference_sam.machine_type_id = reference_sam.machine.machine_type_id
        reference_sam.save(update_fields=["machine_type"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0025_remove_stampingreferencesam_brand_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingreferencesam',
            name='machine_type',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingmachinetype',
            ),
        ),
        migrations.RunPython(backfill_machine_type, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='stampingreferencesam',
            name='machine_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingmachinetype',
            ),
        ),
    ]
