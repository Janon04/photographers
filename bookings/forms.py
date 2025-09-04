# Booking forms
from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
	class Meta:
		model = Booking
		fields = ['photographer', 'service_type', 'date', 'time', 'location']

	def clean(self):
		cleaned_data = super().clean()
		photographer = cleaned_data.get('photographer')
		date = cleaned_data.get('date')
		time = cleaned_data.get('time')
		if photographer and date and time:
			from .models import Booking
			exists = Booking.objects.filter(
				photographer=photographer,
				date=date,
				time=time,
				status__in=['pending', 'confirmed']
			)
			if self.instance.pk:
				exists = exists.exclude(pk=self.instance.pk)
			if exists.exists():
				raise forms.ValidationError('This photographer is already booked for the selected date and time.')
		return cleaned_data
