from django.db import migrations

OLD_KEY = 'home-stamping-coordinator'
NEW_KEY = 'HomeStampingCoordinator'


def fix_key(apps, schema_editor):
    HomeView = apps.get_model('core', 'HomeView')
    HomeView.objects.filter(key=OLD_KEY).update(key=NEW_KEY)


def revert_key(apps, schema_editor):
    HomeView = apps.get_model('core', 'HomeView')
    HomeView.objects.filter(key=NEW_KEY).update(key=OLD_KEY)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_backfill_role_home_view_from_appsetting'),
    ]

    operations = [
        migrations.RunPython(fix_key, revert_key),
    ]
