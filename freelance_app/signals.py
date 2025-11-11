from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, Response, Notification, UserCategory, UserProfile


# --- 1. Новая задача ---
@receiver(post_save, sender=Task)
def notify_new_task(sender, instance, created, **kwargs):
    if created and instance.category:
        # Находим всех пользователей, у кого эта категория выбрана
        user_categories = UserCategory.objects.filter(category=instance.category)
        for uc in user_categories:
            profile = uc.profile
            if profile.wants_task_notifications:
                Notification.objects.create(
                    user=profile.user,
                    type="Новая задача",
                    content=f"Новая задача в категории '{instance.category.name}': {instance.title}",
                )


# --- 2. Новый отклик на задачу ---
@receiver(post_save, sender=Response)
def notify_task_response(sender, instance, created, **kwargs):
    if created:
        task = instance.task
        Notification.objects.create(
            user=task.customer,
            type="Отклик",
            content=f"Новый отклик на вашу задачу: {task.title} от пользователя {instance.executor.username}",
        )
