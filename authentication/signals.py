from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, CustomerProfile, ProviderProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 'customer':
            CustomerProfile.objects.create(user=instance, phone='', location='')
        elif instance.user_type == 'provider':
            ProviderProfile.objects.create(
                user=instance,
                skills='',
                service_area='',
                hourly_rate=0.0,
                location=''
            )
