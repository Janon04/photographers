from django import forms
from .models import BlogComment

class BlogCommentForm(forms.ModelForm):
    author_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name (optional for guests)'}))
    author_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email (optional for guests)'}))

    class Meta:
        model = BlogComment
        fields = ['text', 'author_name', 'author_email']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Add a comment...', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            # Hide name/email fields for authenticated users
            self.fields['author_name'].widget = forms.HiddenInput()
            self.fields['author_email'].widget = forms.HiddenInput()
            self.fields['author_name'].required = False
            self.fields['author_email'].required = False
        else:
            # Make name required for anonymous users
            self.fields['author_name'].required = True
