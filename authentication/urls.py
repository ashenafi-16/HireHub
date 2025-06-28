# urls.py
from django.urls import path
from .views import (
    RegisterView, 
    CustomerProfileView, 
    ProviderProfileView,
    LoginView,
    LogoutView,
    VerifyEmail,
    RequestPasswordResetEmail,
    PasswordTokenCheckAPI,
    SetNewPasswordAPIView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('complete-customer-profile/', CustomerProfileView.as_view(), name='complete-customer-profile'),
    path('complete-provider-profile/', ProviderProfileView.as_view(), name='complete-provider-profile'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('email-verify/', VerifyEmail.as_view(), name="email-verify"),

    path('request-reset-email/', RequestPasswordResetEmail.as_view(), name="request-reset-email"),
    path('password-reset/<uidb64>/<token>/', PasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path('password-reset-complete/', SetNewPasswordAPIView.as_view(), name='password-reset-complete')
]
