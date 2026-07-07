import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

STAMPING_PROCESS_NAMES = [
    "Pulpo Automatico 1",
    "Pulpo Automatico 2",
    "Pulpo Manual",
    "Transfer",
    "Calandra",
]


def seed_stamping_processes(apps, schema_editor):
    StampingProcess = apps.get_model("stamping", "StampingProcess")
    for name in STAMPING_PROCESS_NAMES:
        StampingProcess.objects.create(name=name)


def unseed_stamping_processes(apps, schema_editor):
    StampingProcess = apps.get_model("stamping", "StampingProcess")
    StampingProcess.objects.filter(name__in=STAMPING_PROCESS_NAMES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0007_alter_additionalstampingtime_process_description_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StampingProcess',
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
        migrations.RunPython(seed_stamping_processes, unseed_stamping_processes),
    ]
