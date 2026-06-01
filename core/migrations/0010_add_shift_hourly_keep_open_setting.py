from django.db import migrations


def add_setting(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSetting.objects.create(
        name='Mantener registro hora visible al registrar',
        key='S_H_KEEP_OPEN',
        value='false',
        data_type='BOOLEAN',
        description='Si está activo, el componente de registro hora permanece visible después de registrar dentro de la ventana.',
    )


def remove_setting(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    AppSetting.objects.filter(key='S_H_KEEP_OPEN').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_appsetting_key'),
    ]

    operations = [
        migrations.RunPython(add_setting, remove_setting),
    ]
