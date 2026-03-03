from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag_platform.core'
    verbose_name = 'Core RAG System'
