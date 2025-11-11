from django.apps import AppConfig

class FreelanceAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "freelance_app"

    def ready(self):
        import freelance_app.signals  # <-- подключаем сигналы
