from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class PasswordResetToken(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_token'

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()
