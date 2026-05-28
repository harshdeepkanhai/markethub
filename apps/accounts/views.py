from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from .forms import RegisterForm
from . import services

def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = services.register_user(
            email=form.cleaned_data["email"],
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password1"],
            role=form.cleaned_data["role"]
        )
        login(request, user)
        return redirect("catalog:home")
    return render(request, "accounts/register.html", {"form": form})

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next", "catalog:home"))
    return render(request, "accounts/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("catalog:home")