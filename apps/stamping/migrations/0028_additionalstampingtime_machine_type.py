import django.db.models.deletion
from django.db import migrations, models


def backfill_machine_type(apps, schema_editor):
    AdditionalStampingTime = apps.get_model("stamping", "AdditionalStampingTime")

    for additional_time in AdditionalStampingTime.objects.select_related("machine").all():
        additional_time.machine_type_id = additional_time.machine.machine_type_id
        additional_time.save(update_fields=["machine_type"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0027_remove_stampingreferencesam_machine'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalstampingtime',
            name='machine_type',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='additional_stamping_times',
                to='stamping.stampingmachinetype',
            ),
        ),
        migrations.RunPython(backfill_machine_type, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='additionalstampingtime',
            name='machine_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='additional_stamping_times',
                to='stamping.stampingmachinetype',
            ),
        ),
    ]
