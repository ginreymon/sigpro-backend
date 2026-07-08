import django.db.models.deletion
from django.db import migrations, models


def migrate_machine_data(apps, schema_editor):
    AdditionalStampingTime = apps.get_model("stamping", "AdditionalStampingTime")
    StampingMachine = apps.get_model("stamping", "StampingMachine")

    for additional_time in AdditionalStampingTime.objects.all():
        machine = StampingMachine.objects.get(name=additional_time.machine)
        additional_time.machine_new_id = machine.id
        additional_time.save(update_fields=["machine_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0011_stampingreferencesam_machine_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalstampingtime',
            name='machine_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='additional_stamping_times',
                to='stamping.stampingmachine',
            ),
        ),
        migrations.RunPython(migrate_machine_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='additionalstampingtime',
            name='machine',
        ),
        migrations.RenameField(
            model_name='additionalstampingtime',
            old_name='machine_new',
            new_name='machine',
        ),
        migrations.AlterField(
            model_name='additionalstampingtime',
            name='machine',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='additional_stamping_times',
                to='stamping.stampingmachine',
            ),
        ),
    ]
