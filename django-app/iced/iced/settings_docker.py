DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "iced",
        "USER": "root",
        "PASSWORD": "berkeley",
        "HOST": "database",
        "PORT": "3306",
    },
    "options": {
        "init_command": "SET default_storage_engine=INNODB",
    },
}
