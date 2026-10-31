from django.urls import path

from apps.common.views.op_progress_view import OpProgressView
from apps.common.views.work_session_view import WorkSessionView

urlpatterns = [
    path("op-progress/", OpProgressView.as_view(), name="dashboard-op-progress"),
    path("work-sessions/", WorkSessionView.as_view(), name="dashboard-work-sessions"),
]
