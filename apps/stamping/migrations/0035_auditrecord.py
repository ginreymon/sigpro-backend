import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stamping', '0034_rename_sam_single_person_to_sam'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('op_number', models.IntegerField(blank=True, null=True)),
                ('op_rowid', models.BigIntegerField(blank=True, null=True)),
                ('op_type', models.CharField(blank=True, max_length=10, null=True)),
                ('color', models.CharField(max_length=100)),
                ('sku_rowids', models.JSONField()),
                ('ordered_quantity', models.PositiveIntegerField()),
                ('audited_quantity', models.PositiveIntegerField()),
                ('total_op_quantity', models.PositiveIntegerField()),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
