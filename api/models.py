from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


# Create your models here.

class Group(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False, unique=True)

class UserManager(BaseUserManager):
    def create_user(self, email, password):
        """
        Cria um usuário, dado um email e uma senha.
        """
        if not email:
            raise ValueError("Usuários devem ter um email.")
        if not password:
            raise ValueError("Usuários devem ter uma senha.")

        user = self.model(
            email = self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """
        Cria um super usuário, dado um email e uma senha. É utilizada apenas pelo admin.
        """
        user = self.create_user(
            email = self.normalize_email(email),
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    email = models.EmailField(max_length=100, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    

    objects = UserManager()
    
    def __str__(self):
        return self.email
    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True




class Event(models.Model):
    EVENT_LEVEL = (
        ('error', 'error'),
        ('warning', 'warning'),
        ('debug', 'debug'),
    )

    level = models.CharField(
        max_length=20, choices=EVENT_LEVEL
    )
    title = models.CharField(max_length=50)
    details = models.TextField()
    origin = models.CharField(max_length=150, blank=False, null=False)
    frequency = models.IntegerField(default=1)
    date = models.DateTimeField(auto_now=True)
    shelved = models.BooleanField(default=False)
    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=False, null=False
    )
    group_id = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        blank=False, null=False
    )


def validate_level_choice(sender, instance, **kwargs):
    valid_types = [t[0] for t in sender.EVENT_LEVEL]
    if instance.level not in valid_types:
        raise ValidationError(
            'Event level "{}" is not one of the permitted choices: {}'.format(
                instance.level,
               ', '.join(valid_types)))

# Fazer a validação do Choices no Backend
models.signals.pre_save.connect(validate_level_choice, sender=Event)