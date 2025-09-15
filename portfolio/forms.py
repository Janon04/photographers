# Portfolio forms

from django import forms
from .models import Photo, Category, Story, Event

# Form for creating/updating an event
class EventForm(forms.ModelForm):
	class Meta:
		model = Event
		fields = ['title', 'description', 'date', 'location']

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
		fields = ['image', 'video']
