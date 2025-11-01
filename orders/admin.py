from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'is_paid')
    list_filter = ('is_paid', 'created_at')
    search_fields = ('user__username',)
    inlines = [OrderItemInline]  

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
