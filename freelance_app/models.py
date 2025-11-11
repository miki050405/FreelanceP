from django.db import models
from django.contrib.auth.models import User


# --------------------------
# Профиль пользователя
# --------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    rating = models.FloatField(default=0)
    qr_code = models.ImageField(upload_to="qrcodes/", blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    wants_task_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# --------------------------
# Категории
# --------------------------
class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class UserCategory(models.Model):
    profile = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="categories"
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.profile.user.username} - {self.category.name}"


# --------------------------
# Задачи
# --------------------------
class Task(models.Model):
    STATUS_CHOICES = [
        ("Открыта", "Открыта"),
        ("В работе", "В работе"),
        ("Завершена", "Завершена"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Открыта")
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tasks_created"
    )
    executor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_executed",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# --------------------------
# Отклики / Заявки
# --------------------------
class Response(models.Model):
    STATUS_CHOICES = [
        ("Отклонена", "Отклонена"),
        ("Рассматривается", "Рассматривается"),
        ("Принята", "Принята"),
    ]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="responses")
    executor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="responses"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Рассматривается"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("task", "executor")

    def __str__(self):
        return f"{self.executor.username} → {self.task.title} ({self.status})"


# --------------------------
# Портфолио
# --------------------------
class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolio")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    image = models.ImageField(upload_to="portfolio/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


# --------------------------
# Отзывы / Оценки
# --------------------------
class Review(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_written"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_received"
    )
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# --------------------------
# Платежи
# --------------------------
class Payment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)
    payer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payments_made"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payments_received"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    receipt = models.FileField(upload_to="payments/")


# --------------------------
# Чат
# --------------------------
class Chat(models.Model):
    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chats_started"
    )
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chats_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_sent"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    expires_at = models.DateTimeField(
        null=True, blank=True
    )  # можно использовать для автоматической очистки


# --------------------------
# Уведомления
# --------------------------
class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ("Отклик", "Отклик"),
        ("Новая задача", "Новая задача"),
        ("Статус заявки", "Статус заявки"),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=50, choices=NOTIF_TYPE_CHOICES)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
