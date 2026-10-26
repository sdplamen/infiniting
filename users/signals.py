from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from users.models import Photographer

UserModel = get_user_model()

@receiver(post_save, sender=UserModel)
def create_profile(sender: UserModel, instance: UserModel, created: bool, **kwargs: dict) -> None:
    if created:
        Photographer.objects.create(user=instance,)

@receiver(post_delete, sender=Photographer)
def delete_user_on_photographer_profile_delete(sender, instance, **kwargs):
    if instance.user_id and UserModel.objects.filter(pk=instance.user_id).exists():
        try:
            instance.user.delete()
            print(f'User {instance.user.username} deleted due to Photographer profile deletion.')
        except Exception as e:
            print(f'Error deleting user {instance.user.username} after Photographer profile deletion: {e}')
    else:
        print(f'User associated with Photographer {instance.user_id} already deleted or does not exist.')