import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


DATA_TYPES = [
    ("STRING", "String"),
    ("INTEGER", "Integer"),
    ("DECIMAL", "Decimal"),
    ("BOOLEAN", "Boolean"),
    ("JSON", "JSON"),
]


def seed_data_types_and_migrate_values(apps, schema_editor):
    AppSettingDataType = apps.get_model('core', 'AppSettingDataType')
    AppSetting = apps.get_model('core', 'AppSetting')

    type_by_code = {}
    for code, name in DATA_TYPES:
        obj, _ = AppSettingDataType.objects.get_or_create(code=code, defaults={'name': name})
        type_by_code[code] = obj

    for setting in AppSetting.objects.all():
        setting.data_type = type_by_code.get(setting.data_type_old) or type_by_code['STRING']
        setting.save(update_fields=['data_type'])


def reverse_migrate_values(apps, schema_editor):
    AppSetting = apps.get_model('core', 'AppSetting')
    for setting in AppSetting.objects.all():
        setting.data_type_old = setting.data_type.code if setting.data_type_id else 'STRING'
        setting.save(update_fields=['data_type_old'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_alter_groupoption_table'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppSettingDataType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=50)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'core_app_setting_data_type',
                'ordering': ['code'],
            },
        ),
        migrations.RenameField(
            model_name='appsetting',
            old_name='data_type',
            new_name='data_type_old',
        ),
        migrations.AddField(
            model_name='appsetting',
            name='data_type',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='app_settings',
                to='core.appsettingdatatype',
            ),
        ),
        migrations.RunPython(seed_data_types_and_migrate_values, reverse_migrate_values),
        migrations.RemoveField(
            model_name='appsetting',
            name='data_type_old',
        ),
        migrations.AlterField(
            model_name='appsetting',
            name='data_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='app_settings',
                to='core.appsettingdatatype',
            ),
        ),
    ]
