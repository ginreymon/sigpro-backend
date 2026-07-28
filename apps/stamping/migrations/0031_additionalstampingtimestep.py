import core.models.audit_model
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0030_stampingrecordadditionaltime'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalStampingTimeStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField()),
                ('description', models.CharField(max_length=255)),
                ('standard_time', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('additional_stamping_time', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='stamping.additionalstampingtime')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['additional_stamping_time', 'order'],
            },
            bases=(core.models.audit_model.SpanishUniqueErrorMixin, models.Model),
        ),
    ]
