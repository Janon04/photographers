# Community forms
from django import forms
from .models import ContentReport
class ContentReportForm(forms.ModelForm):
	class Meta:
		model = ContentReport
		fields = ['reason']
		widgets = {
			'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Why are you reporting this content? (optional)'}),
		}

