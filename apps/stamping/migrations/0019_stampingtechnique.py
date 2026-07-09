import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

STAMPING_TECHNIQUES = [
    "ALTA",
    "ALTA DENSIDAD",
    "OFM",
    "PLANO",
    "PLANO Y ALTA",
    "PLANO Y PUFF",
    "PLANO Y SHIMMER",
    "TRANSFER",
]


def seed_techniques(apps, schema_editor):
    StampingTechnique = apps.get_model("stamping", "StampingTechnique")
    for name in STAMPING_TECHNIQUES:
        StampingTechnique.objects.create(name=name)


def unseed_techniques(apps, schema_editor):
    StampingTechnique = apps.get_model("stamping", "StampingTechnique")
    StampingTechnique.objects.filter(name__in=STAMPING_TECHNIQUES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0018_stampingreferencesam_fabric_type_fk'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StampingTechnique',
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
        migrations.RunPython(seed_techniques, unseed_techniques),
    ]
