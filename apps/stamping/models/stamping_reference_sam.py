from decimal import ROUND_HALF_UP, Decimal
from django.db import models
from core.models import AuditModel
from .stamping_machine_type import StampingMachineType
from .stamping_piece import StampingPiece
from .stamping_location import StampingLocation
from .stamping_stamp_type_description import StampingStampTypeDescription
from .stamping_fabric_type import StampingFabricType
from .stamping_technique import StampingTechnique
from .stamping_layout_form import StampingLayoutForm


class StampingReferenceSam(AuditModel):
    rowid_item = models.BigIntegerField(db_index=True, null=True, blank=True)  # production_skuitemlocal.rowid_item
    identification = models.CharField(max_length=50, unique=True)  # excel col A (REFERENCIA)
    machine_type = models.ForeignKey(StampingMachineType, on_delete=models.PROTECT, related_name='reference_sams')
    people_count = models.IntegerField()
    piece = models.ForeignKey(StampingPiece, on_delete=models.PROTECT, related_name='reference_sams')
    stamped_pieces = models.IntegerField(null=True, blank=True)
    location = models.ForeignKey(StampingLocation, on_delete=models.PROTECT, null=True, blank=True, related_name='reference_sams')
    stamp_type_description = models.ForeignKey(StampingStampTypeDescription, on_delete=models.PROTECT, null=True, blank=True, related_name='reference_sams')
    technique = models.ForeignKey(StampingTechnique, on_delete=models.PROTECT, null=True, blank=True, related_name='reference_sams')
    fabric_type = models.ForeignKey(StampingFabricType, on_delete=models.PROTECT, null=True, blank=True, related_name='reference_sams')
    frames = models.IntegerField(null=True, blank=True)
    inks = models.IntegerField(null=True, blank=True)
    prints = models.IntegerField(null=True, blank=True)
    pieces_per_board = models.IntegerField(null=True, blank=True)
    layout_form = models.ForeignKey(StampingLayoutForm, on_delete=models.PROTECT, null=True, blank=True, related_name='reference_sams')
    pre_dried = models.IntegerField(null=True, blank=True)
    sam = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        db_table = "stamping_stamping_reference_sam"
        ordering = ["identification"]

    def __str__(self):
        return self.identification

    @property
    def tasks_per_hour(self):
        if not self.sam:
            return None
        return int((Decimal("60") / self.sam).to_integral_value(rounding=ROUND_HALF_UP))
