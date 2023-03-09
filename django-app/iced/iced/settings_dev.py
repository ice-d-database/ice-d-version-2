DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "iced",
        "USER": "root",
        "PASSWORD": "berkeley",
        "HOST": "127.0.0.1",
        "PORT": "3306",
    },
    "options": {
        "init_command": "SET default_storage_engine=INNODB",
    },
}


ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]  # nosec

DEBUG = True
