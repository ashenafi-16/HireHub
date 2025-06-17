from rest_framework import serializers
from .models import User, CustomerProfile, ProviderProfile
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode


class CustomerRegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=True, write_only=True)
    location = serializers.CharField(required=False, write_only=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'phone', 'location']

    def validate(self, attrs):
        if not attrs.get('username', '').isalnum():
            raise serializers.ValidationError("Username must be alphanumeric")
        return attrs

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        location = validated_data.pop('location', '')

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            user_type='customer'
        )
        CustomerProfile.objects.create(user=user, phone=phone, location=location)
        return user
    
class ProviderRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    skills = serializers.CharField(write_only=True, required=True)
    service_area = serializers.CharField(write_only=True, required=True)
    hourly_rate = serializers.DecimalField(write_only=True, max_digits=6, decimal_places=2, required=True)
    location = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password',
            'skills', 'service_area', 'hourly_rate', 'location'
        ]

    def validate(self, attrs):
        if not attrs['username'].isalnum():
            raise serializers.ValidationError({"username": "Username must be alphanumeric."})
        return attrs

    def create(self, validated_data):
        # Extract ProviderProfile fields
        skills = validated_data.pop('skills')
        service_area = validated_data.pop('service_area')
        hourly_rate = validated_data.pop('hourly_rate')
        location = validated_data.pop('location')
        password = validated_data.pop('password')

        # Create user
        user = User.objects.create_user(**validated_data, user_type='provider')
        user.set_password(password)
        user.save()

        # Create associated ProviderProfile
        ProviderProfile.objects.create(
            user=user,
            skills=skills,
            service_area=service_area,
            hourly_rate=hourly_rate,
            location=location
        )

        return user
class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)

    class Meta:
        model = User
        fields = ['token']


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    username = serializers.CharField(read_only=True)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'password', 'username', 'tokens']

    def get_tokens(self, obj):
        user = User.objects.get(email=obj['email'])
        return user.tokens()

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        user = auth.authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed('Invalid credentials')
        if not user.is_active:
            raise AuthenticationFailed('Account disabled')
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')

        return {
            'email': user.email,
            'username': user.username,
            'tokens': user.tokens()
        }


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)
    redirect_url = serializers.CharField(max_length=500, required=False)


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('Invalid reset link', 401)
            user.set_password(password)
            user.save()
            return user
        except Exception:
            raise AuthenticationFailed('Invalid reset link', 401)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['phone', 'location']

class ProviderProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderProfile
        fields = ['skills', 'service_area', 'hourly_rate', 'location']