from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("production", "0018_productionrecord_net_duration"),
    ]

    operations = [
        migrations.AddField(
            model_name="workbreakrecord",
            name="resumed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
