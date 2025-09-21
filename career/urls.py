from django.urls import path
from .views import CareerPredictView,CareerHistoryView,GoogleAuthView,RegisterUserView,LoginView,CareerDetailsView

urlpatterns = [
    path('predict/', CareerPredictView.as_view(), name='predict'),
    path("history/", CareerHistoryView.as_view(), name="career-history"),
    path("auth/google/", GoogleAuthView.as_view(), name="google_auth"),
    path("login/",LoginView.as_view(),name="login"),
    path("register/",RegisterUserView.as_view(),name="register"),
    path("career/",CareerDetailsView.as_view(),name="career")
]
