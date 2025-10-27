from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Count
from .models import UserProfile, Task, Response, Review
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .forms import UserForm, UserProfileForm
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from .models import Task
from .forms import TaskForm

def home_view(request):
    return render(request, "home.html")


@login_required
def profile_view(request):
    # TODO: потом заменить на request.user
    user = request.user

    profile, _ = UserProfile.objects.get_or_create(user=user)

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
    user = request.user
    # для редактирования лучше гарантировать наличие профиля
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
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


def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            # создаём профиль
            UserProfile.objects.get_or_create(user=user)

            login(request, user)
            return redirect("profile")

    else:
        form = UserRegisterForm()

    return render(request, "register.html", {"form": form})


from django.contrib.auth import authenticate, login, logout


def login_view(request):
    show_error = False

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("profile")
        else:
            show_error = True

    return render(request, "login.html", {"show_error": show_error})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.customer = request.user
            task.save()
            return redirect("profile")
    else:
        form = TaskForm()
    return render(request, "task_form.html", {"form": form})

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, customer=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = TaskForm(instance=task)
    return render(request, "task_form.html", {"form": form})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, customer=request.user)
    if request.method == "POST":
        task.delete()
        return redirect("profile")
    return render(request, "task_confirm_delete.html", {"task": task})

@login_required
def tasks_list(request):
    tasks = Task.objects.all().order_by("-created_at")
    return render(request, "tasks_list.html", {"tasks": tasks})
