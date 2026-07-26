from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_remove_module_has_shifts'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='is_home_target',
            field=models.BooleanField(default=False),
        ),
    ]
