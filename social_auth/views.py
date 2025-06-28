from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from rest_framework.response import Response
from rest_framework import status
from .serializers import AccessTokenOnlySocialLoginSerializer


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    serializer_class = AccessTokenOnlySocialLoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            token = response.data.get("key")
            user = self.user  # Set by `LoginMixin` in dj-rest-auth

            # Determine redirect URL based on user type
            if hasattr(user, "user_type"):
                if user.user_type == "customer":
                    redirect_url = "/complete-customer-profile/"
                elif user.user_type == "provider":
                    redirect_url = "/complete-provider-profile/"
                else:
                    redirect_url = "/"
            else:
                redirect_url = "/"

            return Response({
                "message": "User logged in successfully via Facebook",
                "key": token,
                "redirect_url": redirect_url
            }, status=status.HTTP_200_OK)

        return response


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    serializer_class = AccessTokenOnlySocialLoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            token = response.data.get("key")
            user = self.user  # Set by LoginMixin in dj-rest-auth

            # Determine redirect URL based on user type
            if hasattr(user, "user_type"):
                if user.user_type == "customer":
                    redirect_url = "/complete-customer-profile/"
                elif user.user_type == "provider":
                    redirect_url = "/complete-provider-profile/"
                else:
                    redirect_url = "/"
            else:
                redirect_url = "/"

            return Response({
                "message": "User logged in successfully via Google",
                "key": token,
                "redirect_url": redirect_url
            }, status=status.HTTP_200_OK)

        return response
