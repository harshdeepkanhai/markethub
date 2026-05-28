# MarketHub

A full-featured Django marketplace application demonstrating core and advanced Django concepts — authentication, REST APIs, product catalog, orders, reviews, and real-time notifications.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Setup & Installation](#setup--installation)
3. [Django Concepts Covered](#django-concepts-covered)
   - [Settings & Configuration](#1-settings--configuration)
   - [Apps Architecture](#2-apps-architecture)
   - [Models & ORM](#3-models--orm)
   - [Custom User Model](#4-custom-user-model)
   - [URLs & Routing](#5-urls--routing)
   - [Views](#6-views)
   - [Templates](#7-templates)
   - [Middleware](#8-middleware)
   - [Context Processors](#9-context-processors)
   - [Static & Media Files](#10-static--media-files)
   - [Admin Interface](#11-admin-interface)
   - [Authentication & Authorization](#12-authentication--authorization)
   - [Django REST Framework](#13-django-rest-framework)
   - [JWT Authentication](#14-jwt-authentication)
   - [Filtering, Search & Ordering](#15-filtering-search--ordering)
   - [Signals](#16-signals)
   - [WSGI & ASGI](#17-wsgi--asgi)
   - [Environment Variables](#18-environment-variables)
4. [Tech Stack](#tech-stack)

---

## Project Structure

```
markethub/
├── config/                  # Django project configuration
│   ├── settings.py          # Global settings
│   ├── urls.py              # Root URL config
│   ├── asgi.py              # ASGI entry point (async/WebSocket)
│   └── wsgi.py              # WSGI entry point (traditional sync)
├── apps/                    # All local Django apps
│   ├── core/                # Shared utilities, middleware, context processors
│   ├── accounts/            # Custom user model, auth views
│   ├── catalog/             # Products, categories
│   ├── orders/              # Cart, checkout, order management
│   ├── reviews/             # Product reviews & ratings
│   └── notifications/       # User notifications
├── templates/               # Global HTML templates
├── static/                  # Project-level static files (CSS, JS, images)
├── manage.py                # Django CLI entry point
└── requirements.txt         # Python dependencies
```

---

## Setup & Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd markethub

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file in the project root
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3

# 5. Apply migrations
python manage.py migrate

# 6. Create a superuser
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

---

## Django Concepts Covered

### 1. Settings & Configuration

[`config/settings.py`](config/settings.py) centralises all project configuration. This project uses `django-environ` to keep secrets out of source control via a `.env` file.

```python
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1'])
DATABASES = {'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')}
```

**Key settings groups:**

| Setting | Purpose |
|---|---|
| `INSTALLED_APPS` | Registers Django built-ins, third-party, and local apps |
| `MIDDLEWARE` | Ordered list of request/response processors |
| `DATABASES` | DB connection (SQLite for dev, PostgreSQL for prod via `DATABASE_URL`) |
| `TEMPLATES` | Template engine config and context processors |
| `STATIC_URL / MEDIA_URL` | URL prefixes for static assets and uploads |
| `REST_FRAMEWORK` | DRF global defaults (auth, permissions, pagination, filters) |

**Docs:** https://docs.djangoproject.com/en/6.0/ref/settings/

---

### 2. Apps Architecture

Django organises code into reusable **apps**. This project uses a `apps/` package to namespace all local apps cleanly, registered in `INSTALLED_APPS` as `'apps.accounts'`, `'apps.catalog'`, etc.

```
apps/
├── core/          # Shared: middleware, context processors, base models
├── accounts/      # Custom User model, login, registration, profile
├── catalog/       # Product & category models, listing views
├── orders/        # Cart sessions, checkout, OrderItem models
├── reviews/       # Product reviews tied to confirmed purchases
└── notifications/ # In-app and email notifications
```

Each app follows the standard Django layout:

```
apps/catalog/
├── __init__.py
├── admin.py       # Admin registration
├── apps.py        # AppConfig
├── models.py      # Database models
├── serializers.py # DRF serializers
├── views.py       # Views / ViewSets
├── urls.py        # App URL patterns
├── filters.py     # django-filter FilterSets
├── signals.py     # Django signals
└── tests/         # Unit & integration tests
```

**Docs:** https://docs.djangoproject.com/en/6.0/ref/applications/

---

### 3. Models & ORM

Django's ORM maps Python classes to database tables. Example from the `catalog` app:

```python
# apps/catalog/models.py
from django.db import models
from apps.accounts.models import User

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', null=True, blank=True,
                               related_name='children', on_delete=models.SET_NULL)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
```

**Common ORM queries:**

```python
# Filtering
Product.objects.filter(category__slug='electronics', price__lte=500)

# Prefetch related to avoid N+1 queries
Product.objects.select_related('seller', 'category').prefetch_related('reviews')

# Aggregation
from django.db.models import Avg
Product.objects.annotate(avg_rating=Avg('reviews__rating'))
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/db/models/

---

### 4. Custom User Model

This project replaces Django's default `User` with a custom model (`AUTH_USER_MODEL = 'accounts.User'`). This must be set **before** the first migration.

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    is_seller = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
```

```python
# config/settings.py
AUTH_USER_MODEL = 'accounts.User'
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/auth/customizing/#substituting-a-custom-user-model

---

### 5. URLs & Routing

The root URLconf in [`config/urls.py`](config/urls.py) delegates to each app's own `urls.py` using `include()`.

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('', include('apps.catalog.urls', namespace='catalog')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    path('api/v1/', include('apps.catalog.api_urls')),   # DRF API endpoints
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

```python
# apps/catalog/urls.py
from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
]
```

**URL namespacing** prevents name collisions between apps. Use `{% url 'catalog:home' %}` in templates or `reverse('catalog:home')` in Python.

**Docs:** https://docs.djangoproject.com/en/6.0/topics/http/urls/

---

### 6. Views

MarketHub uses both **function-based views (FBVs)** and **class-based views (CBVs)**.

**Class-Based Views (preferred for standard CRUD):**

```python
# apps/catalog/views.py
from django.views.generic import ListView, DetailView
from .models import Product

class ProductListView(ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('category', 'seller')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/product_detail.html'
    slug_field = 'slug'
```

**Function-Based View (for custom logic):**

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('catalog:product-detail', slug=product.slug)
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/class-based-views/

---

### 7. Templates

Templates live in `templates/` (project-level) and `apps/<app>/templates/` (app-level). Django's template language supports inheritance, tags, filters, and custom tags.

**Base layout example:**

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}MarketHub{% endblock %}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
</head>
<body>
    {% include 'partials/_navbar.html' %}

    {% if messages %}
        {% for message in messages %}
            <div class="alert alert-{{ message.tags }}">{{ message }}</div>
        {% endfor %}
    {% endif %}

    <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

**Child template:**

```html
<!-- apps/catalog/templates/catalog/product_list.html -->
{% extends 'base.html' %}

{% block title %}Products - MarketHub{% endblock %}

{% block content %}
    {% for product in products %}
        <article>
            <h2><a href="{{ product.get_absolute_url }}">{{ product.name }}</a></h2>
            <p>${{ product.price }}</p>
        </article>
    {% empty %}
        <p>No products found.</p>
    {% endfor %}

    {% include 'partials/_pagination.html' with page_obj=page_obj %}
{% endblock %}
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/templates/

---

### 8. Middleware

Middleware is a hook into Django's request/response cycle. This project includes a custom `RequestTimingMiddleware` in `apps.core`.

```python
# apps/core/middleware.py
import time
import logging

logger = logging.getLogger(__name__)

class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response  # called once on startup

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)  # process the view
        duration_ms = (time.monotonic() - start) * 1000
        logger.debug('%s %s — %.1f ms', request.method, request.path, duration_ms)
        response['X-Request-Duration-Ms'] = f'{duration_ms:.1f}'
        return response
```

Registered in settings (order matters — top runs first on request, last on response):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    ...
    'apps.core.middleware.RequestTimingMiddleware',
]
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/http/middleware/

---

### 9. Context Processors

Context processors inject data into **every** template context automatically. This project uses a `cart` context processor so the cart item count is available site-wide.

```python
# apps/core/context_processors.py
def cart(request):
    cart_data = request.session.get('cart', {})
    item_count = sum(cart_data.values())
    return {
        'cart_item_count': item_count,
        'cart': cart_data,
    }
```

Registered in `settings.py` under `TEMPLATES → OPTIONS → context_processors`:

```python
'apps.core.context_processors.cart',
```

Usage in any template:

```html
<span class="badge">{{ cart_item_count }}</span>
```

**Docs:** https://docs.djangoproject.com/en/6.0/ref/templates/api/#built-in-template-context-processors

---

### 10. Static & Media Files

**Static files** (CSS, JS, images bundled with the project):

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # collectstatic destination
STATICFILES_DIRS = [BASE_DIR / 'static'] # additional source dirs
```

**Media files** (user uploads):

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

In templates:

```html
{% load static %}
<img src="{% static 'images/logo.png' %}">
<img src="{{ product.image.url }}">
```

Serve media in development by adding to `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Docs:** https://docs.djangoproject.com/en/6.0/howto/static-files/

---

### 11. Admin Interface

Django's built-in admin provides a ready-made CRUD interface for all registered models.

```python
# apps/catalog/admin.py
from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'price', 'stock', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'seller__email')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('seller',)
    date_hierarchy = 'created_at'
```

Visit `/admin/` after running `python manage.py createsuperuser`.

**Docs:** https://docs.djangoproject.com/en/6.0/ref/contrib/admin/

---

### 12. Authentication & Authorization

Django's auth system handles login, logout, password management, and permissions. This project customises it with `AbstractUser`.

```python
# config/settings.py
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'catalog:home'
LOGOUT_REDIRECT_URL = 'catalog:home'
```

**Protecting views:**

```python
# Decorator (FBV)
from django.contrib.auth.decorators import login_required, permission_required

@login_required
def my_orders(request): ...

@permission_required('catalog.add_product')
def create_product(request): ...


# Mixin (CBV)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class SellerDashboard(LoginRequiredMixin, UserPassesTestMixin, ListView):
    def test_func(self):
        return self.request.user.is_seller
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/auth/

---

### 13. Django REST Framework

DRF adds a full REST API layer. Global defaults are set in `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

**Serializer example:**

```python
# apps/catalog/serializers.py
from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    avg_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'price',
                  'stock', 'image', 'category', 'category_id', 'avg_rating']
```

**ViewSet example:**

```python
# apps/catalog/views.py
from rest_framework import viewsets, permissions
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'seller')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
```

**Router registration:**

```python
# apps/catalog/api_urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
urlpatterns = router.urls
```

This auto-generates: `GET/POST /api/v1/products/` and `GET/PUT/PATCH/DELETE /api/v1/products/<id>/`.

**Docs:** https://www.django-rest-framework.org/

---

### 14. JWT Authentication

`djangorestframework-simplejwt` provides stateless token-based auth for the API.

```python
# config/urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns += [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

**Usage:**

```bash
# Obtain tokens
POST /api/token/
{"email": "user@example.com", "password": "secret"}
→ {"access": "<jwt>", "refresh": "<jwt>"}

# Use access token
GET /api/v1/products/
Authorization: Bearer <access_token>

# Refresh when expired
POST /api/token/refresh/
{"refresh": "<refresh_token>"}
```

**Docs:** https://django-rest-framework-simplejwt.readthedocs.io/

---

### 15. Filtering, Search & Ordering

`django-filter` integrates with DRF to provide declarative query parameter filtering.

```python
# apps/catalog/filters.py
import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    in_stock  = django_filters.BooleanFilter(field_name='stock', lookup_expr='gt',
                                             label='In stock')

    class Meta:
        model = Product
        fields = ['category', 'seller', 'min_price', 'max_price', 'in_stock']
```

```python
# apps/catalog/views.py
from .filters import ProductFilter

class ProductViewSet(viewsets.ModelViewSet):
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'seller__email']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
```

Example API calls:

```
GET /api/v1/products/?category=1&min_price=10&max_price=200
GET /api/v1/products/?search=wireless+headphones
GET /api/v1/products/?ordering=price
```

**Docs:** https://django-filter.readthedocs.io/

---

### 16. Signals

Django signals allow decoupled apps to react to events (model saves, deletes, user login, etc.).

```python
# apps/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order
from .models import Notification

@receiver(post_save, sender=Order)
def notify_seller_on_new_order(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.product.seller,
            message=f'New order #{instance.id} for "{instance.product.name}"',
        )
```

Connect in the app's `AppConfig.ready()`:

```python
# apps/notifications/apps.py
from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    name = 'apps.notifications'

    def ready(self):
        import apps.notifications.signals  # noqa: F401
```

**Docs:** https://docs.djangoproject.com/en/6.0/topics/signals/

---

### 17. WSGI & ASGI

**WSGI** ([`config/wsgi.py`](config/wsgi.py)) — the traditional synchronous server gateway interface, compatible with Gunicorn, uWSGI.

```python
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
```

**ASGI** ([`config/asgi.py`](config/asgi.py)) — the asynchronous server gateway, required for WebSockets (Django Channels) and async views. Both are configured in this project — `ASGI_APPLICATION` powers Django Channels for real-time notifications.

```python
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_asgi_application()
```

**Deploying with Gunicorn (WSGI):**

```bash
gunicorn config.wsgi:application --workers 4
```

**Deploying with Uvicorn (ASGI):**

```bash
uvicorn config.asgi:application --workers 4
```

**Docs:**
- WSGI: https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
- ASGI: https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/

---

### 18. Environment Variables

`django-environ` reads a `.env` file and converts values to the correct Python types.

```
# .env (never commit this file)
SECRET_KEY=django-insecure-replace-me-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgres://user:password@localhost:5432/markethub
```

| Helper | Example | Result type |
|---|---|---|
| `env('KEY')` | `env('SECRET_KEY')` | `str` |
| `env.bool('KEY')` | `env('DEBUG')` with `(bool, False)` | `bool` |
| `env.list('KEY')` | `env.list('ALLOWED_HOSTS')` | `list` |
| `env.db('KEY')` | `env.db('DATABASE_URL')` | dict for `DATABASES` |

**Docs:** https://django-environ.readthedocs.io/

---

## Tech Stack

| Package | Version | Purpose |
|---|---|---|
| Django | 6.0.5 | Web framework |
| djangorestframework | 3.17.1 | REST API |
| djangorestframework-simplejwt | 5.5.1 | JWT authentication |
| django-environ | 0.13.0 | `.env` file support |
| django-filter | 25.2 | Query parameter filtering |
| django-extensions | 4.1 | Dev utilities (`shell_plus`, `graph_models`) |
| psycopg | 3.3.4 | PostgreSQL adapter |
| PyJWT | 2.13.0 | JWT encoding/decoding |
| asgiref | 3.11.1 | ASGI compatibility layer |
