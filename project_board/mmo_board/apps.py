from django.apps import AppConfig



class MmoBoardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mmo_board'

    def ready(self):
        from . import signals
