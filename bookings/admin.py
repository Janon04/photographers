
from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
	list_display = ('client', 'photographer', 'service_type', 'date', 'status', 'payment_status')
	list_filter = ('status', 'payment_status', 'date')
	search_fields = ('client__email', 'photographer__email', 'service_type')
