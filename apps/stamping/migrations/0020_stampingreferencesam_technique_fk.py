import django.db.models.deletion
from django.db import migrations, models


def migrate_technique_data(apps, schema_editor):
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")
    StampingTechnique = apps.get_model("stamping", "StampingTechnique")

    for reference_sam in StampingReferenceSam.objects.all():
        if not reference_sam.technique:
            continue
        technique = StampingTechnique.objects.get(name=reference_sam.technique)
        reference_sam.technique_new_id = technique.id
        reference_sam.save(update_fields=["technique_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0019_stampingtechnique'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingreferencesam',
            name='technique_new',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingtechnique',
            ),
        ),
        migrations.RunPython(migrate_technique_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='stampingreferencesam',
            name='technique',
        ),
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='technique_new',
            new_name='technique',
        ),
    ]
