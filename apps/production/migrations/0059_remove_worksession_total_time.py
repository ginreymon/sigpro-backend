from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0058_move_employee_local_to_people'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worksession',
            name='total_time',
        ),
    ]
