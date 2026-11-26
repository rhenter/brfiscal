SECRET_KEY = "testes"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "brfiscal.contrib.django",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
USE_TZ = True
