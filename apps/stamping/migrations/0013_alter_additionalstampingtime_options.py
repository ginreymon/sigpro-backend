from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0012_additionalstampingtime_machine_fk'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='additionalstampingtime',
            options={'ordering': ['engineering_code', 'code_number', 'machine__name']},
        ),
    ]
