from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import Favorite, ShoppingCart
from users.forms import CustomUserChangeForm, CustomUserCreationForm
from users.models import Subscription, User


class SubscriptionInline(admin.TabularInline):
    """Inline for subscriptions."""

    model = Subscription
    extra = 0
    fk_name = 'user'


class FavoriteInline(admin.TabularInline):
    """Inline for favorites."""

    model = Favorite
    extra = 0


class ShoppingCartInline(admin.TabularInline):
    """Inline for shopping cart."""

    model = ShoppingCart
    extra = 0


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """"Admin interface for the custom User."""

    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display_links = ('username',)
    list_filter = ('email', 'username')
    list_display = ('email', 'username', 'is_active')
    list_editable = ('is_active',)
    inlines = (SubscriptionInline, FavoriteInline, ShoppingCartInline)
    fieldsets = (
        ('Account', {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser',)}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for subscriptions."""

    list_filter = ('author', 'user')
    list_display = (
        'id',
        'user',
        'author',
    )
    search_fields = ('author__username', 'user__username')
