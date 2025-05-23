from django.shortcuts import render, redirect
from .forms import (
    UserRegistrationForm,
    UserVerificationForm,
    UserLoginForm,
    UserProfileForm,
)
from django.views import View
from django.contrib import messages
from utils import (
    create_otp_email_instance,
    create_otp_phone_number_instance,
    MyBackend
)
from . import tasks
import uuid
import random
from .models import OtpEmail, OtpPhoneNumber, CustomUser
from django.contrib.auth import logout, login
from django.contrib.auth.mixins import LoginRequiredMixin



class UserRegistrationView(View):
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            verification_method = form.cleaned_data["verification_method"]
            email = form.cleaned_data["email"]
            phone_number = form.cleaned_data["phone_number"]
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            password = form.cleaned_data["password"]
            expire_date = 5
            if verification_method == "email":
                token = uuid.uuid4()
                link = (
                    request.build_absolute_uri("/")
                    + f"accounts/user-verification/{token}/"
                )
                tasks.send_otp_by_email_async.delay(email, link, expire_date)
                create_otp_email_instance(email, token, expire_date)
                redirect_method = "register"

            else:
                code = random.randint(1000, 9999)
                tasks.send_otp_by_phone_async.delay(phone_number=phone_number, code=code)
                create_otp_phone_number_instance(phone_number, code, expire_date)
                redirect_method = "verification"

            request.session["user_info"] = {
                "email": email,
                "phone_number": phone_number,
                "verification_method": verification_method,
                "password": password,
                "expire_date": expire_date,
            }

            CustomUser.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                password=password,
            )
            messages.success(
                request,
                "account has been created. please activate your account with code/token that we sent to you!!",
                "success",
            )
            return redirect(f"accounts:user_{redirect_method}")
        return render(request, self.template_name, {"form": form})


class UserVerificationView(View):
    form_class = UserVerificationForm
    template_name = "accounts/verify_user_registration.html"

    def get(self, request, *args, **kwargs):
        token = kwargs.get("token")
        user_info = request.session.get("user_info")
        if token and user_info["verification_method"] == "email":
            otp_field = OtpEmail.objects.filter(token=token)
            user_email = user_info.get("email")
            if otp_field.exists() and user_email == otp_field.first().email:
                if otp_field.first().is_expired:
                    messages.error(request, "Token has been expired!!")
                    otp_field.first().delete()
                    return redirect("home:home")
                user = CustomUser.objects.get(email=user_email)
                user.is_active = True
                user.save()
                messages.success(request, "user has been activated successfully!")
                otp_field.first().delete()
                return redirect("home:home")

            messages.error(request, "invalid token !!!")
            return redirect("account:user_register")
        else:
            form = self.form_class()
            return render(
                request,
                self.template_name,
                {"form": form, "expire_date": user_info["expire_date"]},
            )

    def post(self, request, *args, **kwargs):
        otp_form = self.form_class(request.POST)
        user_info = request.session.get("user_info")
        if otp_form.is_valid():
            phone_number = user_info.get("phone_number")
            otp_field = OtpPhoneNumber.objects.filter(phone_number=phone_number)
            if otp_field.exists() and phone_number == otp_field.first().phone_number:
                if otp_field.first().code == int(otp_form.cleaned_data.get("code")):
                    if otp_field.first().is_expired:
                        messages.error(request, "Token has been expired!!")
                        otp_field.first().delete()
                        return redirect("home:home")
                    user = CustomUser.objects.get(phone_number=phone_number)
                    user.is_active = True
                    user.save()
                    messages.success(request, "user has been activated successfully!")
                    otp_field.first().delete()
                    return redirect("home:home")
                messages.error(request, "Invalid code !!")
                return redirect("accounts:user_verification")
            messages.error(request, "Invalid phone number !!")
            return redirect("accounts:user_verification")
        return render(
            request,
            self.template_name,
            {"form": otp_form, "expire_date": user_info["expire_date"]},
        )


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            logout(request)
            messages.success(request, "you logged out successfully!")
            return redirect("home:home")
        messages.error(request, "you are not logged in !")
        return redirect("home:home")


class LoginView(View):
    class_form = UserLoginForm
    template_name = "accounts/login.html"

    def get(self, request):
        form = self.class_form()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.class_form(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get("password")
            phone_number = form.cleaned_data.get("phone_number")
            user = MyBackend.authenticate(phone_number=phone_number, password=password)
            if user:
                login(request, user)
                messages.success(request, "you logged in successfully!")
                return redirect("home:home")
            messages.error(request, "invalid password!!")
            return redirect("accounts:user_login")
        return render(request, self.template_name, {"form": form})


class UserProfileView(LoginRequiredMixin, View):
    class_form = UserProfileForm
    template_name = "accounts/profile.html"

    def get(self, request):
        form = self.class_form(instance=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = self.class_form(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "changes saved!")
            return redirect("accounts:user_profile")
        messages.error(request, "invalid inputs!")
        return render(request, self.template_name, {"form": form})
