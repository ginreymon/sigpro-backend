from django.contrib import admin

# Register your models here.
from core.models import( Module, Option, GroupOption)

admin.site.register(Module)
admin.site.register(Option)
admin.site.register(GroupOption)
