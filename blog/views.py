from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import BlogPost, BlogComment
from .forms import BlogPostForm
from .comment_forms import BlogCommentForm
from django.db.models import Q
from .models import Category, Tag


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    categories = Category.objects.all()
    tags = Tag.objects.all()
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    if category_id:
        posts = posts.filter(category_id=category_id)
    if tag_id:
        posts = posts.filter(tags__id=tag_id)
    return render(request, 'blog/blog_list.html', {'posts': posts, 'categories': categories, 'tags': tags})


def blog_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, is_published=True)
    comments = post.comments.filter(is_approved=True)
    if request.method == 'POST':
        comment_form = BlogCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            if request.user.is_authenticated:
                comment.author = request.user
            # For anonymous, author remains None
            comment.save()
            return redirect('blog_detail', pk=post.pk)
    else:
        comment_form = BlogCommentForm()
    return render(request, 'blog/blog_detail.html', {'post': post, 'comments': comments, 'comment_form': comment_form})


@login_required
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            blog_post = form.save(commit=False)
            blog_post.owner = request.user
            blog_post.save()
            return redirect('blog_detail', pk=blog_post.pk)
    else:
        form = BlogPostForm()
    return render(request, 'blog/blog_form.html', {'form': form})


@login_required
def blog_edit(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog_detail', pk=post.pk)
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'blog/blog_form.html', {'form': form, 'edit': True})
