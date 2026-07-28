from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0032_migrate_process_description_to_steps'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='additionalstampingtime',
            name='process_description',
        ),
    ]
