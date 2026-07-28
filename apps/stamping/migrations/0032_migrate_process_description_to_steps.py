from django.db import migrations


def forwards(apps, schema_editor):
    AdditionalStampingTime = apps.get_model('stamping', 'AdditionalStampingTime')
    AdditionalStampingTimeStep = apps.get_model('stamping', 'AdditionalStampingTimeStep')

    steps = []
    for record in AdditionalStampingTime.objects.exclude(process_description__isnull=True):
        for index, description in enumerate(record.process_description or []):
            if not str(description).strip():
                continue
            steps.append(AdditionalStampingTimeStep(
                additional_stamping_time=record,
                order=index,
                description=description,
                standard_time=None,
                created_by_id=record.created_by_id,
                updated_by_id=record.updated_by_id,
            ))

    AdditionalStampingTimeStep.objects.bulk_create(steps)


def backwards(apps, schema_editor):
    AdditionalStampingTime = apps.get_model('stamping', 'AdditionalStampingTime')
    AdditionalStampingTimeStep = apps.get_model('stamping', 'AdditionalStampingTimeStep')

    for record in AdditionalStampingTime.objects.all():
        ordered_steps = record.steps.order_by('order').values_list('description', flat=True)
        record.process_description = list(ordered_steps) or None
        record.save(update_fields=['process_description'])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0031_additionalstampingtimestep'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
