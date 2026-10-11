class ModuleSerializerExtension:
    """
    Hook that lets another app add fields to ModuleSerializer without
    `production` importing it (stamping depends on production, never the
    reverse). The extending app registers an instance from its AppConfig.ready().

    Subclasses override what they need:
      get_fields()                   extra serializer fields (read and/or write)
      extract(validated_data)        pops this extension's keys, returns state
      apply(module, state)           runs after the module is saved
    """

    def get_fields(self) -> dict:
        return {}

    def extract(self, validated_data: dict):
        return None

    def apply(self, module, state) -> None:
        pass


module_extensions: list[ModuleSerializerExtension] = []


def register_module_extension(extension: ModuleSerializerExtension) -> None:
    if not any(type(e) is type(extension) for e in module_extensions):
        module_extensions.append(extension)
