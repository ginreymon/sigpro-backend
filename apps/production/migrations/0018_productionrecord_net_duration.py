from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0017_remove_productionrecord_server_now_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productionrecord',
            name='net_duration',
            field=models.DurationField(blank=True, null=True),
        ),
    ]
