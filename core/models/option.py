from django.db import models
from .base_entity import BaseEntity
from .module import Module


class Option(BaseEntity):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="options")
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    visible = models.BooleanField(default=True)
    is_home_target = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.module} [{self.order}] {self.name}'
