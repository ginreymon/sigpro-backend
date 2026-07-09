import django.db.models.deletion
from django.db import migrations, models

PIECE_ALIASES = {
    "DELANTERO / POSTERIOR": "DELANTERO/POSTERIOR",
}


def migrate_piece_data(apps, schema_editor):
    StampingReferenceSam = apps.get_model("stamping", "StampingReferenceSam")
    StampingPiece = apps.get_model("stamping", "StampingPiece")

    for reference_sam in StampingReferenceSam.objects.all():
        name = PIECE_ALIASES.get(reference_sam.piece, reference_sam.piece)
        piece = StampingPiece.objects.get(name=name)
        reference_sam.piece_new_id = piece.id
        reference_sam.save(update_fields=["piece_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('stamping', '0014_stamping_reference_sam_catalogs'),
    ]

    operations = [
        migrations.AddField(
            model_name='stampingreferencesam',
            name='piece_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingpiece',
            ),
        ),
        migrations.RunPython(migrate_piece_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='stampingreferencesam',
            name='piece',
        ),
        migrations.RenameField(
            model_name='stampingreferencesam',
            old_name='piece_new',
            new_name='piece',
        ),
        migrations.AlterField(
            model_name='stampingreferencesam',
            name='piece',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='reference_sams',
                to='stamping.stampingpiece',
            ),
        ),
    ]
