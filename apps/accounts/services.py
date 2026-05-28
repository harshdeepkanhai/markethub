from django.db import transaction
from django.utils.text import slugify
from .models import User, VendorProfile

@transaction.atomic
def register_user(*, email, username, password, role=User.Role.BUYER):
    user = User(email=email, username=username, role=role)
    user.set_password(password)  # hash the password before saving
    user.save()
    return user

@transaction.atomic
def become_vendor(*, user, store_name, bio=""):
    user.role = User.Role.VENDOR
    user.save(update_fields=["role"])
    return VendorProfile.objects.create(
        user=user,
        store_name=store_name,
        slug=slugify(store_name),
        bio=bio
    )