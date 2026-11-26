from django.db import migrations

KEY = 'SHOW_ALL_PRODUCTION_ORDERS'


def add_setting(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSettingDataType = apps.get_model('core', 'AppSettingDataType')
    boolean_type, _ = AppSettingDataType.objects.get_or_create(
        code='BOOLEAN', defaults={'name': 'Boolean'}
    )
    AppSetting.objects.get_or_create(
        key=KEY,
        defaults={
            'name': 'Mostrar todas las órdenes de producción',
            'value': 'true',
            'data_type': boolean_type,
            'description': (
                'When enabled, production orders are displayed regardless of audit '
                'authorization, completion status, or other existing status-based '
                'visibility restrictions.'
            ),
        },
    )


def remove_setting(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSetting.objects.filter(key=KEY).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_add_sync_cost_centers_setting'),
    ]

    operations = [
        migrations.RunPython(add_setting, remove_setting),
    ]
