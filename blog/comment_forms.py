from django import forms
from .models import BlogComment

class BlogCommentForm(forms.ModelForm):
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name (optional)'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email (optional)'}))

    class Meta:
        model = BlogComment
        fields = ['text', 'name', 'email']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Add a comment...', 'rows': 3}),
        }
