from apps.stamping.repositories.op_stamping_repository import OPStampingRepository


class OPStampingService:

    @staticmethod
    def get_detalle_estampacion_op_json(tipo_docto, consec_docto):
        return OPStampingRepository.get_detalle_estampacion_op_json(tipo_docto, consec_docto)

    @staticmethod
    def get_trazabilidad_op_json(consec_docto, tipo_docto=None):
        return OPStampingRepository.get_trazabilidad_op_json(consec_docto, tipo_docto)
