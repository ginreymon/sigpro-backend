import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0050_moduleuseraccount'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ModuleWorkBreakRecord',
            new_name='ModuleDowntime',
        ),
        migrations.AlterModelTable(
            name='moduledowntime',
            table='production_module_downtime',
        ),
        migrations.AlterField(
            model_name='moduledowntime',
            name='module',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='module_downtimes',
                to='production.module',
            ),
        ),
        migrations.AlterField(
            model_name='moduledowntime',
            name='work_break',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='module_downtimes',
                to='production.workbreak',
            ),
        ),
    ]
