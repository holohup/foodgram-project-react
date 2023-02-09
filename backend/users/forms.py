from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from users.models import User


class CustomUserCreationForm(UserCreationForm):
    """Custom User creation form."""

    class Meta:
        model = User
        fields = '__all__'


class CustomUserChangeForm(UserChangeForm):
    """Custom User edit form."""

    class Meta:
        model = User
        fields = '__all__'
