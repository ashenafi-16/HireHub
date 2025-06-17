from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CustomerProfile, ProviderProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 'customer':
            CustomerProfile.objects.get_or_create(user=instance)
        elif instance.user_type == 'provider':
            ProviderProfile.objects.get_or_create(user=instance)
