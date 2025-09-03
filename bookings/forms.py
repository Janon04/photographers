# Booking forms
from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
	class Meta:
		model = Booking
		fields = ['photographer', 'service_type', 'date', 'time', 'location']
