import json

from django.db import migrations

HOME_CUSTOM_VIEW_SETTING = 'HOME_ROLE_BASED_VIEWS'


def backfill(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    HomeView = apps.get_model('core', 'HomeView')
    RoleHomeView = apps.get_model('core', 'RoleHomeView')
    Group = apps.get_model('auth', 'Group')

    qs = AppSetting.objects.filter(key=HOME_CUSTOM_VIEW_SETTING, is_active=True)
    if not qs.exists():
        qs = AppSetting.objects.filter(name=HOME_CUSTOM_VIEW_SETTING, is_active=True)
    raw = qs.values_list('value', flat=True).first()
    if not raw:
        return

    try:
        mapping = json.loads(raw)  # { "ComponentKey": [group_id1, group_id2, ...] }
    except (ValueError, TypeError):
        return

    for component_key, group_ids in mapping.items():
        home_view, _ = HomeView.objects.get_or_create(
            key=component_key,
            defaults={'label': component_key},
        )
        for group_id in group_ids:
            if not Group.objects.filter(pk=group_id).exists():
                continue
            RoleHomeView.objects.get_or_create(
                group_id=group_id,
                defaults={'home_view': home_view},
            )


def unbackfill(apps, schema_editor):
    RoleHomeView = apps.get_model('core', 'RoleHomeView')
    HomeView = apps.get_model('core', 'HomeView')
    RoleHomeView.objects.all().delete()
    HomeView.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_homeview_rolehomeview'),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
