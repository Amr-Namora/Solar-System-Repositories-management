from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification, PushToken
from .push import send_push_notification

@receiver(post_save, sender=Notification)
def notify_on_create(sender, instance, created, **kwargs):
    if created and instance.user:
        tokens = list(
            PushToken.objects.filter(user=instance.user, is_active=True)
            .values_list('token', flat=True)
        )
        send_push_notification(tokens, title="New Notification", body=instance.message)