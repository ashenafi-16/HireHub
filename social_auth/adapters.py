from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import CustomerProfile, ProviderProfile  # adjust this import as needed
from authentication.utils import Util

User = get_user_model()

# --------------------------
# Custom Account Adapter
# --------------------------
class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user

        if user.is_authenticated:
            # If user has no role set yet, redirect to role selection
            if not hasattr(user, 'user_type') or not user.user_type:
                return reverse('set-user-type')

            if user.user_type == 'customer':
                profile, _ = CustomerProfile.objects.get_or_create(user=user)
                if not profile.is_profile_complete:
                    return reverse('customer-profile')

            elif user.user_type == 'provider':
                profile, _ = ProviderProfile.objects.get_or_create(user=user)
                if not profile.is_profile_complete:
                    return reverse('provider-profile')

        return reverse('dashboard')


# --------------------------
# Custom Social Account Adapter
# --------------------------
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        
        if not user.can_login:
            if user.user_type == 'customer':
                messages.warning(request, 'Please verify your email before logging in.')
            elif user.user_type == 'provider':
                if not user.is_verified:
                    messages.warning(request, 'Please verify your email before logging in.')
                elif user.status == 'pending':
                    messages.warning(request, 'Your account is pending admin approval.')
                elif user.status == 'rejected':
                    messages.error(request, 'Your account has been rejected by admin.')
            return reverse('account_logout')
        
        if not user.user_type:
            return reverse('set-user-type')
            
        return reverse('customer-profile') if user.user_type == 'customer' else reverse('provider-profile')

    def pre_social_login(self, request, sociallogin):
        if request.user.is_authenticated:
            return

        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        
        if not user.is_verified:
            token = RefreshToken.for_user(user).access_token
            current_site = get_current_site(request).domain
            relative_link = reverse('email-verify')
            absurl = f'http://{current_site}{relative_link}?token={token}'

            email_data = {
                'email_body': f"""
                Hi {user.username},

                Thank you for registering with HireHub. Please verify your email address by clicking the link below:

                {absurl}

                If you did not create this account, please ignore this email.

                Best regards,
                HireHub Team
                """,
                'to_email': user.email,
                'email_subject': 'Verify your HireHub account'
            }
            Util.send_email(email_data)
            messages.success(request, 'Please check your email to verify your account.')
        
        return user
