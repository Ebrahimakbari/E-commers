from django.shortcuts import render, redirect
from .forms import UserRegistrationForm, UserVerificationForm
from django.views import View
from django.contrib import messages
from utils import send_otp_by_email, send_otp_by_phone, create_otp_email_instance, create_otp_phone_number_instance
import uuid
import random
from .models import OtpEmail, OtpPhoneNumber, CustomUser
from django.contrib.auth import logout




class UserRegistrationView(View):
    form_class = UserRegistrationForm

    def get(self, request):
        form = self.form_class()
        return render(request, "accounts/register.html", {"form": form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            verification_method = form.cleaned_data["verification_method"]
            email = form.cleaned_data["email"]
            phone_number = form.cleaned_data["phone_number"]
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            password = form.cleaned_data['password']
            if verification_method == "email":
                token = uuid.uuid4()
                link = request.build_absolute_uri("/") + f"accounts/user-verification/{token}/"
                send_otp_by_email(email, link)
                create_otp_email_instance(email, token, 10)
                redirect_method = 'register'

            else:
                code = random.randint(1000, 9999)
                send_otp_by_phone(phone_number=phone_number, code=code)
                create_otp_phone_number_instance(phone_number, code, 10)
                redirect_method = 'verification'

            request.session["user_info"] = {
                "email": email,
                "phone_number": phone_number,
                "first_name": first_name,
                "last_name": last_name,
                "verification_method": verification_method,
                "password":password,
            }

            CustomUser.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                password=password
            )
            messages.success(
                request,
                "account has been created \n please activate your account with code/token that we sent to you!!",
                "success",
            )
            return redirect(f"accounts:user_{redirect_method}")
        return render(request, "accounts/register.html", {"form": form})


class UserVerificationView(View):
    form_class = UserVerificationForm
    def get(self, request, *args, **kwargs):
        token = kwargs.get("token")
        if token and request.session.get("user_info")['verification_method'] == "email":
            otp_field = OtpEmail.objects.filter(token=token)
            user_info = request.session.get("user_info")
            user_email = user_info.get("email")
            if otp_field.exists() and user_email == otp_field.first().email:
                if otp_field.first().is_expired:
                    messages.error(request, 'Token has been expired!!')
                    return redirect('home:home')
                user = CustomUser.objects.get(email=user_email)
                user.is_active = True
                user.save()
                messages.success(request, 'user has been activated successfully!')
                otp_field.first().delete()
                return redirect('home:home')

            messages.error(request, "invalid token !!!")
            return redirect("account:user_register")
        else:
            form = self.form_class()
            return render(
                request, "accounts/verify_user_registration.html", {"form": form}
            )


    def post(self, request, *args, **kwargs):
        otp_form = self.form_class(request.POST)
        if otp_form.is_valid():
            user_info = request.session.get('user_info')
            phone_number = user_info.get('phone_number')
            otp_field = OtpPhoneNumber.objects.filter(phone_number=phone_number)
            if otp_field.exists() and phone_number == otp_field.first().phone_number:
                if otp_field.first().code == int(otp_form.cleaned_data.get('code')):
                    if otp_field.first().is_expired:
                        messages.error(request, 'Token has been expired!!')
                        return redirect('home:home')
                    user = CustomUser.objects.get(phone_number=phone_number)
                    user.is_active = True
                    user.save()
                    messages.success(request, 'user has been activated successfully!')
                    otp_field.first().delete()
                    return redirect('home:home')
                messages.error(request, 'Invalid code !!')
                return redirect('accounts:user_verification')
            messages.error(request, 'Invalid phone number !!')
            return redirect('accounts:user_verification')
        return render(
            request, "accounts/verify_user_registration.html", {"form": otp_form}
        )


class LogoutView(View):
    def get(self,request):
        user = request.user
        if user.is_authenticated:
            logout(request)
            messages.success(request, 'you logged out successfully!')
            return redirect('home:home')
        messages.error(request, 'you are not logged in !')
        return redirect('home:home')


class LoginView(View):
    def get(self, request):
        pass
    
    def post(self, request):
        pass
