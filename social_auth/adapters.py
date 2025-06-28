from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from allauth.account.utils import user_email

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return  # Already associated with a user

        email = sociallogin.account.extra_data.get("email") or user_email(sociallogin.user)
        if not email:
            return

        try:
            user = User.objects.get(email__iexact=email)

            sociallogin.connect(request, user)

            if not user.is_verified:
                user.is_verified = True
                user.save(update_fields=["is_verified"])

        except User.DoesNotExist:
            print(f"[Adapter] No user found with email: {email}. A new one will be created.")

    def save_user(self, request, sociallogin, form=None):
       
        user = super().save_user(request, sociallogin, form)

        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        return user
