# Booking forms
from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
	client_name = forms.CharField(max_length=100, required=False, label="Your Name")
	client_email = forms.EmailField(required=False, label="Your Email")
	client_phone = forms.CharField(max_length=30, required=False, label="Phone Number")

	class Meta:
		model = Booking
		fields = ['photographer', 'service_type', 'date', 'time', 'location']

	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		super(BookingForm, self).__init__(*args, **kwargs)
		if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
			self.fields.pop('client_name', None)
			self.fields.pop('client_email', None)
			self.fields.pop('client_phone', None)
		else:
			self.fields['client_name'].required = True
			self.fields['client_email'].required = True

	def clean(self):
		cleaned_data = super().clean()
		# Allow double-booking: do not check for existing bookings at the same date/time
		return cleaned_data
