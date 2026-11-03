from django.db import migrations, models


class Migration(migrations.Migration):
    """Additive and nullable: existing TEP details keep their data and simply
    have no time traceability (null)."""

    dependencies = [
        ('integration', '0006_delete_siesaoutbounddocument'),
    ]

    operations = [
        migrations.AddField(
            model_name='tepdetail',
            name='time_mode',
            field=models.CharField(
                blank=True, choices=[('real', 'Real'), ('standard', 'Estándar')], max_length=10, null=True
            ),
        ),
        migrations.AddField(
            model_name='tepdetail',
            name='sent_seconds_per_unit',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name='tepdetail',
            name='real_seconds_by_unit',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True),
        ),
    ]
