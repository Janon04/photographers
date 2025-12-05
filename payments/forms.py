# Payment forms
from django import forms
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
import re


class CardPaymentForm(forms.Form):
	"""Form for card payment validation"""
	card_number = forms.CharField(
		max_length=19,
		validators=[
			RegexValidator(
				regex=r'^\d{4}\s?\d{4}\s?\d{4}\s?\d{3,4}$',
				message='Enter a valid card number'
			)
		],
		widget=forms.TextInput(attrs={
			'class': 'form-input',
			'placeholder': '1234 5678 9012 3456',
			'maxlength': '19'
		})
	)
	
	card_expiry = forms.CharField(
		max_length=5,
		validators=[
			RegexValidator(
				regex=r'^\d{2}/\d{2}$',
				message='Enter expiry as MM/YY'
			)
		],
		widget=forms.TextInput(attrs={
			'class': 'form-input',
			'placeholder': 'MM/YY',
			'maxlength': '5'
		})
	)
	
	card_cvv = forms.CharField(
		max_length=4,
		validators=[
			RegexValidator(
				regex=r'^\d{3,4}$',
				message='Enter a valid CVV'
			)
		],
		widget=forms.TextInput(attrs={
			'class': 'form-input',
			'placeholder': '123',
			'maxlength': '4'
		})
	)
	
	cardholder_name = forms.CharField(
		max_length=100,
		validators=[
			RegexValidator(
				regex=r'^[a-zA-Z\s]+$',
				message='Enter a valid name (letters and spaces only)'
			)
		],
		widget=forms.TextInput(attrs={
			'class': 'form-input',
			'placeholder': 'John Doe'
		})
	)
	
	def clean_card_number(self):
		"""Validate card number using Luhn algorithm"""
		card_number = self.cleaned_data['card_number'].replace(' ', '')
		
		# Basic validation
		if not card_number.isdigit():
			raise ValidationError('Card number must contain only digits')
		
		if len(card_number) < 13 or len(card_number) > 19:
			raise ValidationError('Card number must be 13-19 digits')
		
		# Luhn algorithm
		def luhn_check(card_num):
			digits = [int(d) for d in card_num]
			checksum = digits.pop()
			digits.reverse()
			doubled = [d * 2 if i % 2 == 0 else d for i, d in enumerate(digits)]
			summed = sum(d - 9 if d > 9 else d for d in doubled)
			return (summed + checksum) % 10 == 0
		
		if not luhn_check(card_number):
			raise ValidationError('Invalid card number')
		
		return card_number
	
	def clean_card_expiry(self):
		"""Validate expiry date"""
		from datetime import datetime
		expiry = self.cleaned_data['card_expiry']
		month, year = expiry.split('/')
		
		try:
			month = int(month)
			year = int('20' + year)
		except ValueError:
			raise ValidationError('Invalid expiry date')
		
		if month < 1 or month > 12:
			raise ValidationError('Invalid month')
		
		# Check if expired
		now = datetime.now()
		if year < now.year or (year == now.year and month < now.month):
			raise ValidationError('Card has expired')
		
		return expiry


class MobileMoneyPaymentForm(forms.Form):
	"""Form for mobile money payment validation"""
	PROVIDER_CHOICES = [
		('', 'Choose your provider'),
		('mtn', 'MTN Mobile Money'),
		('airtel', 'Airtel Money'),
	]
	
	momo_provider = forms.ChoiceField(
		choices=PROVIDER_CHOICES,
		widget=forms.Select(attrs={'class': 'form-input'})
	)
	
	momo_phone = forms.CharField(
		max_length=20,
		validators=[
			RegexValidator(
				regex=r'^\+?250\s?\d{3}\s?\d{3}\s?\d{3}$',
				message='Enter a valid Rwanda phone number (+250 XXX XXX XXX)'
			)
		],
		widget=forms.TextInput(attrs={
			'class': 'form-input',
			'placeholder': '+250 XXX XXX XXX'
		})
	)
	
	def clean_momo_phone(self):
		"""Normalize phone number"""
		phone = self.cleaned_data['momo_phone']
		# Remove all spaces and formatting
		phone = re.sub(r'\s+', '', phone)
		
		# Ensure it starts with +250
		if not phone.startswith('+250'):
			if phone.startswith('250'):
				phone = '+' + phone
			elif phone.startswith('0'):
				phone = '+250' + phone[1:]
			else:
				phone = '+250' + phone
		
		# Validate length
		if len(phone) != 13:  # +250 + 9 digits
			raise ValidationError('Phone number must be 9 digits')
		
		return phone


class PayPalPaymentForm(forms.Form):
	"""Form for PayPal payment validation"""
	paypal_email = forms.EmailField(
		validators=[EmailValidator(message='Enter a valid email address')],
		widget=forms.EmailInput(attrs={
			'class': 'form-input',
			'placeholder': 'your@email.com'
		})
	)
	
	def clean_paypal_email(self):
		"""Validate PayPal email"""
		email = self.cleaned_data['paypal_email']
		
		# Additional PayPal-specific validation if needed
		if len(email) > 254:
			raise ValidationError('Email address is too long')
		
		return email.lower()


class BankTransferPaymentForm(forms.Form):
	"""Form for bank transfer payment validation"""
	bank_reference = forms.CharField(
		max_length=100,
		validators=[
			RegexValidator(
				regex=r'^[A-Z0-9\-]+$',
				message='Enter a valid reference number (letters, numbers, and hyphens only)'
			)
		],
		widget=forms.TextInput(attrs={
			'class': 'form-input',
			'placeholder': 'Enter payment reference'
		})
	)
	
	def clean_bank_reference(self):
		"""Validate and normalize bank reference"""
		reference = self.cleaned_data['bank_reference']
		return reference.upper().strip()
