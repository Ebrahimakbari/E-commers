from django.core.mail import EmailMessage
import datetime
from django.utils import timezone
from accounts.models import OtpEmail, OtpPhoneNumber
from kavenegar import *
from decouple import config
from django.contrib.auth.mixins import UserPassesTestMixin



class IsAdminUserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin



def send_otp_by_phone(phone_number, code):
    try:
        api = KavenegarAPI(config("OTP_SMS_CODE"))
        params = {
            "sender": config("SENDER_PHONE"),
            "receptor": str(phone_number),
            "message": f"کد تایید شما : {code}",
        }
        response = api.sms_send(params)
    except APIException as e:
        print(e, response)
    except HTTPException as e:
        print(e, response)


def send_otp_by_email(email, link, expire_date):
    e_mail = EmailMessage(
        "Verify Account",
        f"to verify email click on this link:{link} \n token expires in {expire_date} minutes!",
        to=[email],
    )
    e_mail.send()


def create_otp_phone_number_instance(phone_number, code, expiration_minutes=5):
    expiration_time = timezone.now() + datetime.timedelta(minutes=expiration_minutes)
    otp = OtpPhoneNumber.objects.create(
        phone_number=phone_number, code=code, expires_at=expiration_time
    )
    otp.save()
    return otp


def create_otp_email_instance(email, token, expiration_minutes=5):
    expiration_time = timezone.now() + datetime.timedelta(minutes=expiration_minutes)
    otp = OtpEmail.objects.create(email=email, token=token, expires_at=expiration_time)
    otp.save()
    return otp
