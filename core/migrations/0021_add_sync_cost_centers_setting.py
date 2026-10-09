from django.db import migrations

KEY = 'SYNC_COST_CENTERS'


def add_setting(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSettingDataType = apps.get_model('core', 'AppSettingDataType')
    string_type, _ = AppSettingDataType.objects.get_or_create(
        code='STRING', defaults={'name': 'String'}
    )
    AppSetting.objects.get_or_create(
        key=KEY,
        defaults={
            'name': 'Centros de costo sincronizados desde el ERP',
            'value': '110,103,109,102',
            'data_type': string_type,
            'description': (
                'Lista separada por comas de f284_rowid de centros de costo del ERP cuyos '
                'empleados sincroniza sp_sync_terceros (110, 103 = producción/corte; '
                '109, 102 = estampación). La lee dbo.fn_centros_costo_permitidos(); si la '
                'clave no existe o no tiene ningún entero válido, la función usa esta misma '
                'lista por defecto. Quitar un centro de costo aquí desactiva (soft delete) '
                'a sus empleados en el siguiente sync.'
            ),
        },
    )


def remove_setting(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSetting.objects.filter(key=KEY).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_fix_home_stamping_coordinator_key'),
    ]

    operations = [
        migrations.RunPython(add_setting, remove_setting),
    ]
