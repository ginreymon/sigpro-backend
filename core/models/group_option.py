from django.db import models
from django.contrib.auth.models import Group
from .option import Option


class GroupOption(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_options")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name="group_options")

    class Meta:
        unique_together = ("group", "option")

    def __str__(self):
        return f"{self.group.name} - [{self.option.order}] {self.option.name}"
