from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- Constants ---
AUTH_PROVIDERS = {
    'facebook': 'facebook',
    'google': 'google',
    'twitter': 'twitter',
    'email': 'email',
}

USER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('provider', 'Provider'),
)

USER_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

# --- Custom User Manager ---
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, user_type='customer', **extra_fields):
        if not username:
            raise TypeError('Users should have a username')
        if not email:
            raise TypeError('Users should have an email')

        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            user_type=user_type,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        if password is None:
            raise TypeError('Superusers must have a password')

        user = self.create_user(
            username=username,
            email=email,
            password=password,
            user_type='customer',  # superuser type is still 'customer'
            **extra_fields
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

# --- Custom User Model ---
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_profile_complete = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=USER_STATUS_CHOICES, default='pending')
    auth_provider = models.CharField(
        max_length=255,
        default=AUTH_PROVIDERS.get('email'),
        blank=False,
        null=False
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.user_type})"

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @property
    def can_login(self):
        if self.user_type == 'customer':
            return self.is_verified
        elif self.user_type == 'provider':
            return self.is_verified and self.status == 'approved'
        return False

# --- Customer Profile ---
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customerprofile')
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100, blank=True)
    is_profile_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"CustomerProfile - {self.user.email}"

# --- Provider Profile ---
class ProviderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='providerprofile')
    skills = models.TextField(blank=True)
    service_area = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    location = models.CharField(max_length=100)
    is_profile_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"ProviderProfile - {self.user.email}"

# --- Signal Handlers to Auto-Create Profiles ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create user profile.
    Only creates profile if user_type is set and profile doesn't exist.
    """
    if created and instance.user_type:
        try:
            if instance.user_type == 'customer':
                CustomerProfile.objects.get_or_create(
                    user=instance,
                    defaults={
                        'phone': '',
                        'location': '',
                        'is_profile_complete': False
                    }
                )
            elif instance.user_type == 'provider':
                ProviderProfile.objects.get_or_create(
                    user=instance,
                    defaults={
                        'skills': '',
                        'service_area': '',
                        'hourly_rate': 0.00,
                        'location': '',
                        'is_profile_complete': False
                    }
                )
        except Exception as e:
            # Log the error but don't raise it
            print(f"Error creating profile: {e}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal handler to save user profile.
    Only saves if profile exists.
    """
    try:
        if instance.user_type == 'customer' and hasattr(instance, 'customerprofile'):
            instance.customerprofile.save()
        elif instance.user_type == 'provider' and hasattr(instance, 'providerprofile'):
            instance.providerprofile.save()
    except Exception as e:
        # Log the error but don't raise it
        print(f"Error saving profile: {e}")
