from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0026_stampingreferencesam_machine_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stampingreferencesam',
            name='machine',
        ),
    ]
