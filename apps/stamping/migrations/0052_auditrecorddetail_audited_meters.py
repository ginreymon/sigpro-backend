from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0051_additional_time_standard_time_minutes'),
    ]

    operations = [
        migrations.AddField(
            model_name='auditrecorddetail',
            name='audited_meters',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
