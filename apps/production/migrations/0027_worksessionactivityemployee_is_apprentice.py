from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("production", "0026_worksession_editing_finalized"),
    ]

    operations = [
        migrations.AddField(
            model_name="worksessionactivityemployee",
            name="is_apprentice",
            field=models.BooleanField(default=False),
        ),
    ]
