import jwt
import os
from .utils import Util
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,views,generics
from django.urls import reverse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from .models import CustomerProfile, ProviderProfile
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .serializers import (
    RegisterSerializer, 
    CustomerProfileSerializer, 
    ProviderProfileSerializer,
    EmailVerificationSerializer,
    SetNewPasswordSerializer,
    ResetPasswordEmailRequestSerializer,
)

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        absurl = f'http://{current_site}{relative_link}?token={access_token}&refresh_token={refresh}'

        if user.user_type == 'customer':
            redirect_url = '/complete-customer-profile/'
        elif user.user_type == 'provider':
            redirect_url = '/complete-provider-profile/'
        else:
            redirect_url = '/'
        
        email_body = f"Hi {user.email},\nUse the link below to verify your email:\n{absurl}"
        email_data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Verify your email'
        }
        Util.send_email(email_data)

        return Response({
            'message': 'User registered successfully',
            'user_type': user.user_type,
            'access_token': access_token,
            'redirect_url': redirect_url
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        profile_complete = False
        redirect_url = '/'

        if user.user_type == 'customer':
            try:
                profile = user.customerprofile
                profile_complete = profile.is_profile_complete
                redirect_url = '/login/' if profile_complete else '/complete-customer-profile/'
            except CustomerProfile.DoesNotExist:
                redirect_url = '/complete-customer-profile/'

        elif user.user_type == 'provider':
            try:
                profile = user.providerprofile
                profile_complete = profile.is_profile_complete
                redirect_url = '/login/' if profile_complete else '/complete-provider-profile/'
            except ProviderProfile.DoesNotExist:
                redirect_url = '/complete-provider-profile/'
        if not user.is_verified:
            return Response({"detail": "Email address is not verified. Please verify your email before proceeding."},status=status.HTTP_403_FORBIDDEN)
        
        if not profile.is_profile_complete:
            return Response({"detail": "Please complete your profile to proceed."},status=status.HTTP_403_FORBIDDEN)

        return Response({
            'refresh': str(refresh),
            'access': access_token,
            'user_type': user.user_type,
            'email': user.email,
            'profile_complete': profile_complete,
            'redirect_url': redirect_url,
        })

class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = get_object_or_404(CustomerProfile, user=request.user)
        serializer = CustomerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_profile_complete=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProviderProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = get_object_or_404(ProviderProfile, user=request.user)
        serializer = ProviderProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_profile_complete=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


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

        return Response({'success': 'If an account exists with this email, a reset link has been sent.'}, status=status.HTTP_200_OK)

class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = [os.environ.get('APP_SCHEME', 'myapp'), 'http', 'https']
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
