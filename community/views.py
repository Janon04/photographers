
from django.shortcuts import render, get_object_or_404
from .models import Post, CommunityCategory

def post_list(request):
	posts = Post.objects.all().select_related('category')
	categories = CommunityCategory.objects.all()
	return render(request, 'community/post_list.html', {'posts': posts, 'categories': categories})

def post_detail(request, pk):
	post = get_object_or_404(Post, pk=pk)
	return render(request, 'community/post_detail.html', {'post': post})
