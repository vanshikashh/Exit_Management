"""
Django settings for Exit_management project.
Reads secrets and DB config from .env file via django-environ.
"""

import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Read .env ────────────────────────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG       = env('DEBUG')

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tasks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Exit_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Exit_management.wsgi.application'

# ─── Database — PostgreSQL via DATABASE_URL in .env ───────────────────────────
DATABASES = {
    'default': env.db('DATABASE_URL')
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL      = 'tasks.CustomUser'
LOGIN_URL            = 'login'
LOGIN_REDIRECT_URL   = 'exit_interview_form'
LOGOUT_REDIRECT_URL  = 'login'

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Jazzmin ──────────────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title":   "Clovia Exit Management",
    "site_header":  "Clovia HR Admin",
    "site_brand":   "Exit Management",
    "site_logo":    None,
    "login_logo":   None,
    "welcome_sign": "Welcome to Clovia Exit Management Admin",
    "copyright":    "Clovia Pvt Ltd",
    "search_model": ["tasks.CustomUser", "tasks.ExitProcess"],
    "topmenu_links": [
        {"name": "Home",      "url": "admin:index",    "permissions": ["auth.view_user"]},
        {"name": "Exit App",  "url": "/hr/dashboard/", "new_window": False},
        {"name": "Audit Log", "url": "/hr/audit-log/", "new_window": False},
    ],
    "show_sidebar":         True,
    "navigation_expanded":  True,
    "icons": {
        "auth":                "fas fa-users-cog",
        "tasks.customuser":    "fas fa-user",
        "tasks.department":    "fas fa-building",
        "tasks.task":          "fas fa-tasks",
        "tasks.employeetask":  "fas fa-check-square",
        "tasks.exitprocess":   "fas fa-sign-out-alt",
        "tasks.exitinterview": "fas fa-file-alt",
        "tasks.auditlog":      "fas fa-history",
    },
    "default_icon_parents":  "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active":  True,
    "custom_css":            "css/admin_custom.css",
    "custom_js":             None,
    "use_google_fonts_cdn":  True,
    "show_ui_builder":       False,
    "changeform_format":     "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":         False,
    "footer_small_text":         False,
    "body_small_text":           False,
    "brand_small_text":          False,
    "brand_colour":              "navbar-primary",
    "accent":                    "accent-primary",
    "navbar":                    "navbar-dark",
    "no_navbar_border":          False,
    "navbar_fixed":              True,
    "layout_boxed":              False,
    "footer_fixed":              False,
    "sidebar_fixed":             True,
    "sidebar":                   "sidebar-dark-primary",
    "sidebar_nav_small_text":    False,
    "sidebar_disable_expand":    False,
    "sidebar_nav_child_indent":  False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style":  False,
    "sidebar_nav_flat_style":    False,
    "theme":                     "default",
    "dark_mode_theme":           None,
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-outline-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
}
