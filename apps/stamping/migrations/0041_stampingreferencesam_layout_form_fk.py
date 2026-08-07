import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_layout_forms(apps, schema_editor):
    """Catalog seeded from whatever layout_form free-text values already
    exist on StampingReferenceSam, instead of a hardcoded list — guarantees
    every live value gets a matching catalog row before the FK backfill."""
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")
    StampingLayoutForm = apps.get_model("stamping", "StampingLayoutForm")

    names = (
        StampingReferenceSam.objects.exclude(layout_form__isnull=True)
        .exclude(layout_form__exact="")
        .values_list("layout_form", flat=True)
        .distinct()
    )
    for name in names:
        StampingLayoutForm.objects.get_or_create(name=name.strip())


def migrate_layout_form_data(apps, schema_editor):
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")
    StampingLayoutForm = apps.get_model("stamping", "StampingLayoutForm")

    for reference_sam in StampingReferenceSam.objects.all():
        if not reference_sam.layout_form:
            continue
        layout_form = StampingLayoutForm.objects.get(name=reference_sam.layout_form.strip())
        reference_sam.layout_form_new_id = layout_form.id
        reference_sam.save(update_fields=["layout_form_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0040_remove_tasks_per_hour_column'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StampingLayoutForm',
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
                'db_table': 'stamping_stamping_layout_form',
            },
        ),
        migrations.RunPython(seed_layout_forms, migrations.RunPython.noop),
        migrations.AddField(
            model_name='stampingreferencesam',
            name='layout_form_new',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampinglayoutform',
            ),
        ),
        migrations.RunPython(migrate_layout_form_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='stampingreferencesam',
            name='layout_form',
        ),
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='layout_form_new',
            new_name='layout_form',
        ),
    ]
