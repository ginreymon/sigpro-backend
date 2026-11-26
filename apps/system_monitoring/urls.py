from django.urls import path

from .views import ClientErrorView, DiagnosticsView, SiesaCheckView, SummaryView

urlpatterns = [
    path("summary/", SummaryView.as_view()),
    path("diagnostics/", DiagnosticsView.as_view()),
    path("integrations/siesa/check/", SiesaCheckView.as_view()),
    path("client-errors/", ClientErrorView.as_view()),
]
