from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from recipes.models import Favorite, ShoppingCart

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import Subscription

CustomUser = get_user_model()


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fk_name = 'user'


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display_links = ('username',)
    list_filter = ('email', 'username')
    list_display = ('email', 'username', 'is_active')
    list_editable = ('is_active',)
    inlines = [SubscriptionInline, FavoriteInline, ShoppingCartInline]
    fieldsets = (
        ('Account', {'fields': ('username', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (('Permissions'), {
            'fields': ('is_active', 'is_superuser',),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_filter = ('author', 'user')
    list_display = ('id', 'user', 'author',)
    search_fields = ('author__username', 'user__username')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author', 'user')
