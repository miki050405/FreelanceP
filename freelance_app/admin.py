from django.contrib import admin
from .models import (
    UserProfile, Category, UserCategory,
    Task, Response, Portfolio, Review,
    Payment, Chat, Message, Notification
)

# --------------------------
# Профиль пользователя
# --------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "location", "created_at")
    search_fields = ("user__username", "user__email", "phone", "location")

# --------------------------
# Категории
# --------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(UserCategory)
class UserCategoryAdmin(admin.ModelAdmin):
    list_display = ("profile", "category")
    search_fields = ("profile__user__username", "category__name")

# --------------------------
# Задачи
# --------------------------
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "customer", "executor", "price", "deadline", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "description", "customer__username", "executor__username")

# --------------------------
# Отклики
# --------------------------
@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("task", "executor", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("task__title", "executor__username")

# --------------------------
# Портфолио
# --------------------------
@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "link", "created_at")
    search_fields = ("title", "user__username")

# --------------------------
# Отзывы
# --------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "receiver", "rating", "created_at")
    search_fields = ("task__title", "author__username", "receiver__username", "comment")

# --------------------------
# Платежи
# --------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("task", "payer", "receiver", "amount", "payment_date")
    search_fields = ("task__title", "payer__username", "receiver__username")

# --------------------------
# Чат
# --------------------------
@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("user1", "user2", "created_at")
    search_fields = ("user1__username", "user2__username")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("chat", "sender", "content", "created_at", "is_read")
    search_fields = ("chat__user1__username", "chat__user2__username", "content")

# --------------------------
# Уведомления
# --------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("user__username", "content")
