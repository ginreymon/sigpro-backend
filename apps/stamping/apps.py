from django.apps import AppConfig


class StampingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.stamping'

    def ready(self):
        from apps.production.serializers.module_extensions import register_module_extension
        from apps.stamping.serializers.module_machine_extension import ModuleMachineExtension

        register_module_extension(ModuleMachineExtension())
