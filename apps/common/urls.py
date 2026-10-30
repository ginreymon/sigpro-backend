from django.urls import path

from apps.common.views.op_progress_view import OpProgressView

urlpatterns = [
    path("op-progress/", OpProgressView.as_view(), name="dashboard-op-progress"),
]
