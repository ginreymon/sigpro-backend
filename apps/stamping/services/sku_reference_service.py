from apps.stamping.repositories.sku_reference_repository import SkuReferenceRepository


class SkuReferenceService:

    @staticmethod
    def get_references() -> list[dict]:
        return SkuReferenceRepository.get_references()
