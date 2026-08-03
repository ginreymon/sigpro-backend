from django.db import migrations


def add_setting(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSetting.objects.create(
        name='Ventana de calibración para registro de estampación (minutos)',
        key='STAMPING_CAL_WINDOW',
        value='5',
        data_type='INTEGER',
        description='Minutos alrededor de cada hora en punto durante los cuales app-stamping-record permite guardar/actualizar. Fuera de esta ventana el botón Guardar queda deshabilitado.',
    )


def remove_setting(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSetting.objects.filter(key='STAMPING_CAL_WINDOW').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_option_is_home_target'),
    ]

    operations = [
        migrations.RunPython(add_setting, remove_setting),
    ]
