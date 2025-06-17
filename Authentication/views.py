import os
import jwt
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import smart_bytes, smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User
from .serializers import (
    CustomerRegisterSerializer,
    ProviderRegisterSerializer,
    SetNewPasswordSerializer,
    ResetPasswordEmailRequestSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    LogoutSerializer
)
from .utils import Util
from .renderers import UserRenderer


class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [os.environ.get('APP_SCHEME', 'myapp'), 'http', 'https']


class CustomerRegisterView(generics.GenericAPIView):
    serializer_class = CustomerRegisterSerializer
    renderer_classes = (UserRenderer,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        absurl = f'http://{current_site}{relative_link}?token={token}'

        email_body = f"Hi {user.username},\nUse the link below to verify your email:\n{absurl}"
        email_data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Verify your email'
        }
        Util.send_email(email_data)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProviderRegisterView(generics.GenericAPIView):
    serializer_class = ProviderRegisterSerializer
    renderer_classes = (UserRenderer,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        absurl = f'http://{current_site}{relative_link}?token={token}'

        email_body = f"Hi {user.username},\nUse the link below to verify your email:\n{absurl}"
        email_data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Verify your email'
        }
        Util.send_email(email_data)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='JWT token for email verification', type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = get_object_or_404(User, id=payload['user_id'])

            if not user.is_verified:
                user.is_verified = True
                user.save()

            return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'Activation link expired'}, status=status.HTTP_400_BAD_REQUEST)

        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        if user:
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request).domain
            relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})

            redirect_url = request.data.get('redirect_url', '')
            absurl = f'http://{current_site}{relative_link}?redirect_url={redirect_url}'

            email_body = f"Hello,\nUse the link below to reset your password:\n{absurl}"
            email_data = {
                'email_body': email_body,
                'to_email': user.email,
                'email_subject': 'Reset your password'
            }
            Util.send_email(email_data)

        # Always return success response to prevent email enumeration
        return Response({'success': 'If an account exists with this email, a reset link has been sent.'}, status=status.HTTP_200_OK)


class PasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        redirect_url = request.GET.get('redirect_url', '')
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                # Token invalid or expired
                return CustomRedirect(f'{redirect_url}?token_valid=False')

            return CustomRedirect(
                f'{redirect_url}?token_valid=True&message=Credentials Valid&uidb64={uidb64}&token={token}'
            )
        except DjangoUnicodeDecodeError:
            return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'success': True, 'message': 'Password reset successful'}, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)



from rest_framework import generics, permissions
from .models import CustomerProfile, ProviderProfile
from .serializers import CustomerProfileSerializer, ProviderProfileSerializer

class CompleteCustomerProfileView(generics.UpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.customer_profile

class CompleteProviderProfileView(generics.UpdateAPIView):
    serializer_class = ProviderProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.provider_profile