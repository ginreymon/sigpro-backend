from django.db import models
from .base_entity import BaseEntity    
from .module import Module

class Option(BaseEntity):   
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='options')