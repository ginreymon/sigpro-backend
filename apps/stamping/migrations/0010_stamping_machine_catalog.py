import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

MACHINE_TYPES = [
    "AUTOMATICO",
    "MANUAL",
    "TRANSFER",
    "CALANDRA",
]

# name -> machine type name
MACHINES = {
    "AUTOMATICO": "AUTOMATICO",
    "AUTOMATICO 01": "AUTOMATICO",
    "AUTOMATICO 02": "AUTOMATICO",
    "MANUAL": "MANUAL",
    "TRANSFER": "TRANSFER",
}


def seed_machine_catalog(apps, schema_editor):
    StampingMachineType = apps.get_model("stamping", "StampingMachineType")
    StampingMachine = apps.get_model("stamping", "StampingMachine")

    types_by_name = {}
    for name in MACHINE_TYPES:
        types_by_name[name] = StampingMachineType.objects.create(name=name)

    for name, type_name in MACHINES.items():
        StampingMachine.objects.create(name=name, machine_type=types_by_name[type_name])


def unseed_machine_catalog(apps, schema_editor):
    StampingMachineType = apps.get_model("stamping", "StampingMachineType")
    StampingMachine = apps.get_model("stamping", "StampingMachine")
    StampingMachine.objects.filter(name__in=MACHINES.keys()).delete()
    StampingMachineType.objects.filter(name__in=MACHINE_TYPES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0009_rename_pieces_per_table_and_reference_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StampingMachineType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='StampingMachine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
                ('machine_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='machines', to='stamping.stampingmachinetype')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.RunPython(seed_machine_catalog, unseed_machine_catalog),
    ]
