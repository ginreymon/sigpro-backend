from apps.catalog.repositories.technical_sheet_repository import TechnicalSheetRepository


class TechnicalSheetService:

    @staticmethod
    def get_technical_sheet_json(sheet_id: int):
        return TechnicalSheetRepository.get_technical_sheet_json(sheet_id)

    @staticmethod
    def get_referencias() -> list[dict]:
        return TechnicalSheetRepository.get_referencias()

    @staticmethod
    def get_sku_reference_info(rowid_item: int) -> dict | None:
        return TechnicalSheetRepository.get_sku_reference_info(rowid_item)
