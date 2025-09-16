from ckeditor.widgets import CKEditorWidget

from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
	list_display = ('get_client_display', 'photographer', 'service_type', 'date', 'status', 'payment_status')
	list_filter = ('status', 'payment_status', 'date')
	search_fields = ('client__email', 'client_name', 'photographer__email', 'service_type')
	formfield_overrides = {
		# Uncomment the next line if service_type is a TextField
		# Booking.service_type.field: {'widget': CKEditorWidget},
	}

	def get_client_display(self, obj):
		if obj.client:
			return obj.client.get_full_name() or obj.client.email
		return obj.client_name or obj.client_email or 'Anonymous'
	get_client_display.short_description = 'Client'
