from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStamped

class User(AbstractUser, TimeStamped):
    class Role(models.TextChoices):
        BUYER = "buyer", "Buyer"
        VENDOR = "vendor", "Vendor"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.BUYER)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email" # use email instead of username for authentication
    REQUIRED_FIELDS = ["username"] # username is still required for AbstractUser, but not used for login

    @property
    def is_vendor(self):
        return self.role == self.Role.VENDOR

    def __str__(self):
        return self.email

class VendorProfile(TimeStamped):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor")
    store_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    bio = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False) # admin approval required to start selling
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0) # denormalized average rating from reviews

    def __str__(self):
        return self.store_name
