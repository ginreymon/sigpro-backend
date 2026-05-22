from django.db import models

class BaseEntity(models.Model):
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    creation_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    state = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ['order']

    def __str__(self):
        return f'[{self.order}] {self.name}'
