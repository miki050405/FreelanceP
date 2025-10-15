from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Count
from .models import UserProfile, Task, Response, Review
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .forms import UserForm, UserProfileForm
from django.contrib import messages


def home_view(request):
    return render(request, "home.html")


def profile_view(request):
    # TODO: потом заменить на request.user
    user = get_object_or_404(User, id=1)

    profile = get_object_or_404(UserProfile.objects.select_related("user"), user=user)

    # Счётчики и ОЦЕНКА (средняя по отзывам)
    reviews_agg = Review.objects.filter(receiver=user).aggregate(
        avg=Avg("rating"),
        cnt=Count("id"),
    )

    stats = {
        "active_tasks": Task.objects.filter(customer=user, status="В работе").count(),
        # заявки как ИСПОЛНИТЕЛЬ
        "my_applications": Response.objects.filter(executor=user).count(),
        "task_responses": Response.objects.filter(task__customer=user).count(),
        "unread": 0,  # оставляем как есть, подключим позже
        "reviews_avg": reviews_agg["avg"] or 0,
        "reviews_cnt": reviews_agg["cnt"] or 0,
    }

    # Отзывы с пагинацией (чтобы можно было листать)
    reviews_qs = (
        Review.objects.filter(receiver=user)
        .select_related("author", "task")
        .order_by("-created_at")
    )
    reviews_page = Paginator(reviews_qs, 5).get_page(request.GET.get("rvpage"))

    context = {
        "profile": profile,
        "user_obj": user,
        "stats": stats,
        "reviews_page": reviews_page,
        # пригодится дальше для вкладок Исполнитель/Заказчик
        "my_tasks": Task.objects.filter(customer=user)
        .select_related("category", "executor")
        .order_by("-created_at"),
        "my_responses": Response.objects.filter(executor=user)
        .select_related("task", "task__customer", "task__category")
        .order_by("-created_at"),
    }
    return render(request, "profile.html", context)


def edit_profile(request):
    user = get_object_or_404(User, id=1)
    # для редактирования лучше гарантировать наличие профиля
    profile, _created = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Профиль обновлён ✅")
            return redirect("profile")
        messages.error(request, "Проверь поля формы.")
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    return render(
        request,
        "edit_profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )
