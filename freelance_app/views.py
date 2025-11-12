from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Count
from .models import Category, UserProfile, Task, Response, Review
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from .forms import UserForm, UserProfileForm
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from .models import Task, Response
from .forms import TaskForm
from django.urls import reverse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.db import transaction
from .models import Notification, UserCategory, UserProfile

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
    # все мои заявки
    my_responses = (
        Response.objects.filter(executor=user)
        .select_related("task", "task__customer", "task__category")
        .order_by("-created_at")
    )
    my_responses_pending = (
        Response.objects.filter(executor=user)
        .exclude(status="Принята")
        .select_related("task", "task__customer", "task__category")
        .order_by("-created_at")
    )
    my_assignments = (
        Response.objects.filter(executor=user, status="Принята")
        .select_related("task", "task__customer", "task__category")
        .exclude(task__status="Завершена")
        .order_by("-created_at")
    )
    responses_to_my_tasks = (
        Response.objects.filter(task__customer=user)
        .select_related("task", "task__category", "executor")
        .order_by("-created_at")
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
        "my_tasks": Task.objects.filter(customer=user)
        .select_related("category", "executor")
        .order_by("-created_at"),
        "my_responses": my_responses,
        "my_responses_pending": my_responses_pending,
        "my_assignments": my_assignments,
        "responses_to_my_tasks": responses_to_my_tasks,
        "response_status_choices": Response.STATUS_CHOICES,
    }
    return render(request, "profile.html", context)


@login_required
def profile_public_view(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target)

    reviews_agg = Review.objects.filter(receiver=target).aggregate(
        avg=Avg("rating"), cnt=Count("id")
    )

    # то, что должен видеть гость на чужом профиле:
    my_assignments = (
        Response.objects.filter(executor=target, status="Принята")
        .select_related("task", "task__customer", "task__category")
        .exclude(task__status="Завершена")
        .order_by("-created_at")
    )

    responses_to_my_tasks = (
        Response.objects.filter(task__customer=target)
        .select_related("task", "task__category", "executor")
        .order_by("-created_at")
    )

    my_tasks = (
        Task.objects.filter(customer=target)
        .select_related("category", "executor")
        .order_by("-created_at")
    )

    reviews_qs = (
        Review.objects.filter(receiver=target)
        .select_related("author", "task")
        .order_by("-created_at")
    )
    reviews_page = Paginator(reviews_qs, 5).get_page(request.GET.get("rvpage"))

    context = {
        "profile": profile,
        "user_obj": target,  # важно для шапки профиля
        "is_public": True,  # флаг для шаблона
        "stats": {
            "reviews_avg": reviews_agg["avg"] or 0,
            "reviews_cnt": reviews_agg["cnt"] or 0,
            "my_applications": Response.objects.filter(executor=target).count(),
            "task_responses": responses_to_my_tasks.count(),
            "unread": 0,
        },
        # данные для вкладок
        "my_assignments": my_assignments,
        "responses_to_my_tasks": responses_to_my_tasks,
        "my_tasks": my_tasks,
        # заявки скрываем — в шаблоне просто не выводим этот блок при is_public
        "my_responses_pending": None,
        "response_status_choices": Response.STATUS_CHOICES,
    }
    return render(request, "profile.html", context)


@require_POST
@login_required
def response_set_status(request, pk):
    resp = get_object_or_404(
        Response.objects.select_related("task", "task__customer"), pk=pk
    )

    if resp.task.customer_id != request.user.id:
        messages.error(request, "Нет прав изменять статус этого отклика.")
        return redirect(request.POST.get("next") or "profile")

    new_status = request.POST.get("status")
    valid = dict(Response.STATUS_CHOICES).keys()
    if new_status not in valid:
        messages.error(request, "Некорректный статус.")
        return redirect(request.POST.get("next") or "profile")

    with transaction.atomic():
        if new_status == "Принята":
            # 1) сам отклик
            resp.status = "Принята"
            resp.save(update_fields=["status"])

            # 2) задача — назначаем исполнителя и переводим "В работе"
            task = resp.task
            task.executor = resp.executor
            task.status = "В работе"
            task.save(update_fields=["executor", "status"])

            # 3) остальные отклики на эту задачу отклоняем
            other_responses = Response.objects.filter(task=task).exclude(pk=resp.pk)
            other_responses.update(status="Отклонена")

            #Уведомляем исполнителя, чей отклик принят
            Notification.objects.create(
                user=resp.executor,
                type="Статус заявки",
                content=f"Ваш отклик на задачу '{task.title}' принят!"
            )

            #Уведомляем остальных, что их отклонено
            for r in other_responses:
                Notification.objects.create(
                    user=r.executor,
                    type="Статус заявки",
                    content=f"Ваш отклик на задачу '{task.title}' отклонён."
                )

            messages.success(request, "Отклик принят. Задача переведена в «В работе».")
        else:
            # Любой другой статус (Рассматривается / Отклонена)
            resp.status = new_status
            resp.save(update_fields=["status"])

            # уведомление об изменении статуса
            Notification.objects.create(
                user=resp.executor,
                type="Статус заявки",
                content=f"Статус вашего отклика на задачу '{resp.task.title}' изменён на '{new_status}'"
            )

            messages.success(request, "Статус отклика обновлён.")

    return redirect(request.POST.get("next") or "profile")


@require_POST
@login_required
def response_cancel(request, pk):
    """Исполнитель отменяет свой отклик."""
    resp = get_object_or_404(Response, pk=pk, executor=request.user)

    # удаляем отклик
    resp.delete()
    messages.success(request, "Ваш отклик успешно отменён.")
    return redirect("profile")


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


# @login_required
def tasks_list(request):
    tasks = Task.objects.all().order_by("-created_at")
    return render(request, "tasks_list.html", {"tasks": tasks})


def respond_to_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, is_active=True)

    if not request.user.is_authenticated:
        messages.warning(
            request, "Чтобы откликнуться, нужно зарегистрироваться или войти."
        )
        login_url = reverse("login")
        return redirect(f"{login_url}?next={request.get_full_path()}")

    if task.customer_id == request.user.id:
        messages.error(request, "Ты очень умный, раз хочешь выполнить свою же задачу")
        return redirect("tasks_list")

    if task.status != "Открыта":
        messages.info(request, "Отклик доступен только для открытых задач.")
        return redirect("tasks_list")

    obj, created = Response.objects.get_or_create(
        task=task,
        executor=request.user,
        defaults={"status": "Рассматривается"},
    )
    if created:
        messages.success(request, "Ваша заявка отправлена!")
    else:
        messages.info(request, "Вы уже откликались на эту задачу.")

    return redirect("tasks_list")


@login_required
def create_task(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        price = request.POST.get("price")
        category_id = request.POST.get("category")
        category = Category.objects.get(id=category_id)

        task = Task.objects.create(
            title=title,
            description=description,
            price=price,
            category=category,
            customer=request.user
        )
        
        subscribers = UserCategory.objects.filter(category=category)
        for sub in subscribers:
            if sub.profile.wants_task_notifications:
                Notification.objects.create(
                    user=sub.profile.user,
                    type="Новая задача",
                    content=f"Новая задача в категории '{category.name}': {task.title}",
                )

        messages.success(request, "Задача успешно создана!")
        return redirect("tasks_list")

    categories = Category.objects.all()
    return render(request, "create_task.html", {"categories": categories})

@login_required
def send_response(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        response = Response.objects.create(
            task=task,
            executor=request.user
        )
        Notification.objects.create(
            user=task.customer,
            type="Отклик",
            content=f"{request.user.username} откликнулся на вашу задачу '{task.title}'"
        )

        messages.success(request, "Отклик успешно отправлен!")
        return redirect("task_detail", task_id=task.id)

    return redirect("tasks_list")

@login_required
def update_response_status(request, response_id):
    response = get_object_or_404(Response, id=response_id)
    
    if request.method == "POST":
        new_status = request.POST.get("status")
        response.status = new_status
        response.save()

        # 🔔 уведомляем исполнителя
        Notification.objects.create(
            user=response.executor,
            type="Статус заявки",
            content=f"Статус вашего отклика на задачу '{response.task.title}' изменён на '{new_status}'"
        )

        messages.success(request, "Статус отклика обновлён.")
        return redirect("task_detail", task_id=response.task.id)

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "notifications.html", {"notifications": notifications})

@login_required
def notifications(request):
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})