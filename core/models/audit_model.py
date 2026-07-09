from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class SpanishUniqueErrorMixin:
    # Avoids Django's default message, which interpolates verbose_name (English by default).
    def unique_error_message(self, model_class, unique_check):
        if len(unique_check) == 1:
            return ValidationError('Ya existe un registro con este valor.', code='unique')
        return ValidationError(
            'Ya existe un registro con esta combinación de valores.', code='unique_together'
        )


class UserAuditModel(SpanishUniqueErrorMixin, models.Model):

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True   


class TimeAuditModel(SpanishUniqueErrorMixin, models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveModel(SpanishUniqueErrorMixin, models.Model):

    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AuditModel(UserAuditModel, TimeAuditModel, ActiveModel):
    
    class Meta:
        abstract = True