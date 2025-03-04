from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from .managers import CustomUserManager
from django.utils import timezone




class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=11, unique=True)
    avatar = models.ImageField(upload_to='users/avatar/%Y/%m/%d/', blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
    
    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
    
    @property
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_staff(self):
        return self.is_admin


class OtpPhoneNumber(models.Model):
    phone_number = models.CharField(max_length=11)
    code = models.SmallIntegerField()
    created = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'otp PhoneNumber'
        verbose_name_plural = 'otp PhoneNumbers'
        
    def __str__(self):
        return f"{self.phone_number} - {self.code} - {self.created}"
    
    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at


class OtpEmail(models.Model):
    email = models.EmailField(max_length=50)
    token = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'otp Email'
        verbose_name_plural = 'otp Emails'
        
    def __str__(self):
        return f"{self.email} - {self.token} - {self.created}"
    
    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at