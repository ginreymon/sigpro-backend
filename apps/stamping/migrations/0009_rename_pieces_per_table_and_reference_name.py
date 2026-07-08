from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0008_stampingprocess'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='pieces_per_table',
            new_name='pieces_per_board',
        ),
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='reference_name',
            new_name='identification',
        ),
        migrations.AlterModelOptions(
            name='stampingreferencesam',
            options={'ordering': ['identification']},
        ),
    ]
