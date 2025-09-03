# Portfolio forms

from django import forms
from .models import Photo, Category, Story

class PhotoForm(forms.ModelForm):
	class Meta:
		model = Photo
		fields = ['image', 'title', 'description', 'category']

class CategoryForm(forms.ModelForm):
	class Meta:
		model = Category
		fields = ['name']


# Form for uploading a story
class StoryForm(forms.ModelForm):
	class Meta:
		model = Story
		fields = ['image']
