import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

STAMPING_PIECES = [
    "AMBAS COPAS",
    "AMBAS PIERNAS",
    "COPAS",
    "DELANTERO",
    "DELANTERO/POSTERIOR",
    "ESPALDAS",
    "FRENTES",
    "MARIPOSA",
    "PIERNA",
    "POSTERIOR",
    "REALCE",
]

STAMPING_LOCATIONS = [
    "CENTRO",
    "CENTRO SUPERIOR",
    "COPAS",
    "DERECHA",
    "DERECHA / IZQUIERDA",
    "FULL",
    "IZQUIERDA",
    "LATERAL IZQUIERDO",
    "PIEZA COMPLETA",
]

STAMPING_STAMP_TYPE_DESCRIPTIONS = [
    "FULL",
    "LOCALIZADO",
    "LOCALIZADO/REVOLVER",
    "TERMOFIJADO",
]

STAMPING_FABRIC_TYPES = [
    "ALGODÓN UNICOLOR",
    "GAUDY",
    "MICROFIBRA SUBLIMADO",
    "MICROFIBRA UNICOLOR",
]


def seed_catalogs(apps, schema_editor):
    StampingPiece = apps.get_model("stamping", "StampingPiece")
    StampingLocation = apps.get_model("stamping", "StampingLocation")
    StampingStampTypeDescription = apps.get_model("stamping", "StampingStampTypeDescription")
    StampingFabricType = apps.get_model("stamping", "StampingFabricType")

    for name in STAMPING_PIECES:
        StampingPiece.objects.create(name=name)
    for name in STAMPING_LOCATIONS:
        StampingLocation.objects.create(name=name)
    for name in STAMPING_STAMP_TYPE_DESCRIPTIONS:
        StampingStampTypeDescription.objects.create(name=name)
    for name in STAMPING_FABRIC_TYPES:
        StampingFabricType.objects.create(name=name)


def unseed_catalogs(apps, schema_editor):
    StampingPiece = apps.get_model("stamping", "StampingPiece")
    StampingLocation = apps.get_model("stamping", "StampingLocation")
    StampingStampTypeDescription = apps.get_model("stamping", "StampingStampTypeDescription")
    StampingFabricType = apps.get_model("stamping", "StampingFabricType")

    StampingPiece.objects.filter(name__in=STAMPING_PIECES).delete()
    StampingLocation.objects.filter(name__in=STAMPING_LOCATIONS).delete()
    StampingStampTypeDescription.objects.filter(name__in=STAMPING_STAMP_TYPE_DESCRIPTIONS).delete()
    StampingFabricType.objects.filter(name__in=STAMPING_FABRIC_TYPES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0013_alter_additionalstampingtime_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StampingPiece',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='StampingLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='StampingStampTypeDescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='StampingFabricType',
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
        migrations.RunPython(seed_catalogs, unseed_catalogs),
    ]
