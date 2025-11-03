from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import BlogPost, BlogComment, BlogLike, BlogDislike
from .forms import BlogPostForm
from .comment_forms import BlogCommentForm
from django.db.models import Q
from .models import Category, Tag


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    categories = Category.objects.all()
    tags = Tag.objects.all()
    
    # Filter parameters
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    author_id = request.GET.get('author')
    
    if category_id:
        posts = posts.filter(category_id=category_id)
    if tag_id:
        posts = posts.filter(tags__id=tag_id)
    if author_id:
        posts = posts.filter(owner_id=author_id)
    
    # For logged-in users viewing their own posts, show all posts (including drafts)
    if author_id and request.user.is_authenticated and str(request.user.id) == author_id:
        posts = BlogPost.objects.filter(owner_id=author_id)
    
    posts = posts.order_by('-created_at')
    
    context = {
        'posts': posts, 
        'categories': categories, 
        'tags': tags,
        'current_author': author_id,
    }
    return render(request, 'blog/blog_list.html', context)


def blog_detail(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, is_published=True)
    comments = post.comments.filter(is_approved=True).order_by('-created_at')
    
    # Check if user has liked/disliked this post
    user_liked = False
    user_disliked = False
    
    if request.user.is_authenticated:
        user_liked = BlogLike.objects.filter(post=post, user=request.user).exists()
        user_disliked = BlogDislike.objects.filter(post=post, user=request.user).exists()
    else:
        # Check by session and IP for anonymous users
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        ip_address = get_client_ip(request)
        
        user_liked = BlogLike.objects.filter(
            post=post, 
            session_key=session_key, 
            ip_address=ip_address
        ).exists()
        user_disliked = BlogDislike.objects.filter(
            post=post, 
            session_key=session_key, 
            ip_address=ip_address
        ).exists()
    
    if request.method == 'POST':
        comment_form = BlogCommentForm(request.POST, user=request.user)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            if request.user.is_authenticated:
                comment.author = request.user
            else:
                # For anonymous users, save the name and email
                comment.author_name = comment_form.cleaned_data.get('author_name')
                comment.author_email = comment_form.cleaned_data.get('author_email')
            comment.save()
            messages.success(request, 'Your comment has been added successfully!')
            return redirect('blog_detail', pk=post.pk)
    else:
        comment_form = BlogCommentForm(user=request.user)
    
    context = {
        'post': post, 
        'comments': comments, 
        'comment_form': comment_form,
        'user_liked': user_liked,
        'user_disliked': user_disliked,
    }
    return render(request, 'blog/blog_detail.html', context)


@require_POST
def blog_like(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, is_published=True)
    
    if request.user.is_authenticated:
        # For authenticated users
        like, created = BlogLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            # Already liked, remove the like
            like.delete()
            liked = False
        else:
            liked = True
            # Remove dislike if exists
            BlogDislike.objects.filter(post=post, user=request.user).delete()
    else:
        # For anonymous users
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        ip_address = get_client_ip(request)
        
        like, created = BlogLike.objects.get_or_create(
            post=post, 
            session_key=session_key, 
            ip_address=ip_address
        )
        if not created:
            # Already liked, remove the like
            like.delete()
            liked = False
        else:
            liked = True
            # Remove dislike if exists
            BlogDislike.objects.filter(
                post=post, 
                session_key=session_key, 
                ip_address=ip_address
            ).delete()
    
    return JsonResponse({
        'liked': liked,
        'disliked': False,
        'likes_count': post.total_likes,
        'dislikes_count': post.total_dislikes
    })


@require_POST
def blog_dislike(request, pk):
    post = get_object_or_404(BlogPost, pk=pk, is_published=True)
    
    if request.user.is_authenticated:
        # For authenticated users
        dislike, created = BlogDislike.objects.get_or_create(post=post, user=request.user)
        if not created:
            # Already disliked, remove the dislike
            dislike.delete()
            disliked = False
        else:
            disliked = True
            # Remove like if exists
            BlogLike.objects.filter(post=post, user=request.user).delete()
    else:
        # For anonymous users
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        ip_address = get_client_ip(request)
        
        dislike, created = BlogDislike.objects.get_or_create(
            post=post, 
            session_key=session_key, 
            ip_address=ip_address
        )
        if not created:
            # Already disliked, remove the dislike
            dislike.delete()
            disliked = False
        else:
            disliked = True
            # Remove like if exists
            BlogLike.objects.filter(
                post=post, 
                session_key=session_key, 
                ip_address=ip_address
            ).delete()
    
    return JsonResponse({
        'liked': False,
        'disliked': disliked,
        'likes_count': post.total_likes,
        'dislikes_count': post.total_dislikes
    })


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
