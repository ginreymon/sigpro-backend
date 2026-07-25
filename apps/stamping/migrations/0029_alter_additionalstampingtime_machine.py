import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0028_additionalstampingtime_machine_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='additionalstampingtime',
            name='machine',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='additional_stamping_times',
                to='stamping.stampingmachine',
            ),
        ),
    ]
