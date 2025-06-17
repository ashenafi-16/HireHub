from django.urls import path
from .views import (
    CustomerRegisterView, ProviderRegisterView, LogoutAPIView, SetNewPasswordAPIView,
    VerifyEmail, LoginAPIView, PasswordTokenCheckAPI, RequestPasswordResetEmail
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Separate registration endpoints
    path('register/customer/', CustomerRegisterView.as_view(), name="customer-register"),
    path('register/provider/', ProviderRegisterView.as_view(), name="provider-register"),

    # Auth endpoints
    path('login/', LoginAPIView.as_view(), name="login"),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('email-verify/', VerifyEmail.as_view(), name="email-verify"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Password reset endpoints
    path('request-reset-email/', RequestPasswordResetEmail.as_view(), name="request-reset-email"),
    path('password-reset/<uidb64>/<token>/', PasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path('password-reset-complete/', SetNewPasswordAPIView.as_view(), name='password-reset-complete')
]
