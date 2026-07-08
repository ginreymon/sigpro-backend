import django.db.models.deletion
from django.db import migrations, models


def migrate_machine_data(apps, schema_editor):
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")
    StampingMachine = apps.get_model("stamping", "StampingMachine")

    for reference_sam in StampingReferenceSam.objects.all():
        machine = StampingMachine.objects.get(name=reference_sam.machine)
        reference_sam.machine_new_id = machine.id
        reference_sam.save(update_fields=["machine_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0010_stamping_machine_catalog'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingreferencesam',
            name='machine_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingmachine',
            ),
        ),
        migrations.RunPython(migrate_machine_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='stampingreferencesam',
            name='machine',
        ),
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='machine_new',
            new_name='machine',
        ),
        migrations.AlterField(
            model_name='stampingreferencesam',
            name='machine',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingmachine',
            ),
        ),
    ]
