from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0033_remove_additionalstampingtime_process_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='sam_single_person',
            new_name='sam',
        ),
    ]
