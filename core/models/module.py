from django.db import models
from .base_entity import BaseEntity

class Module(BaseEntity):
    has_shifts = models.BooleanField(default=False) # esta este id en ProductionArea