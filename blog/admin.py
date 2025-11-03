from django.contrib import admin
from .models import Category, Tag, BlogPost, BlogComment, BlogLike, BlogDislike

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'post_count']
    search_fields = ['name']
    ordering = ['name']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Number of Posts'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'post_count']
    search_fields = ['name']
    ordering = ['name']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Number of Posts'

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'category', 'is_published', 'created_at', 'like_count', 'dislike_count', 'comment_count']
    list_filter = ['is_published', 'category', 'tags', 'created_at', 'owner']
    search_fields = ['title', 'content', 'owner__username', 'owner__first_name', 'owner__last_name']
    date_hierarchy = 'created_at'
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at', 'total_likes', 'total_dislikes', 'total_comments']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'owner', 'content')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Publishing', {
            'fields': ('is_published',)
        }),
        ('Statistics', {
            'fields': ('total_likes', 'total_dislikes', 'total_comments'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def like_count(self, obj):
        return obj.total_likes
    like_count.short_description = 'Likes'
    
    def dislike_count(self, obj):
        return obj.total_dislikes
    dislike_count.short_description = 'Dislikes'
    
    def comment_count(self, obj):
        return obj.comments.count()
    comment_count.short_description = 'Comments'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.owner = request.user
        super().save_model(request, obj, form, change)

@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ['short_text', 'author_display', 'post', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at', 'post__category']
    search_fields = ['text', 'author__username', 'author_name', 'post__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Comment Details', {
            'fields': ('post', 'author', 'author_name', 'author_email', 'text')
        }),
        ('Moderation', {
            'fields': ('is_approved',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Comment Text'
    
    def author_display(self, obj):
        return obj.author_display
    author_display.short_description = 'Author'
    
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments were approved.')
    approve_comments.short_description = 'Approve selected comments'
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments were disapproved.')
    disapprove_comments.short_description = 'Disapprove selected comments'


@admin.register(BlogLike)
class BlogLikeAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'user_display', 'created_at']
    list_filter = ['created_at', 'post__category']
    search_fields = ['post__title', 'user__username', 'session_key', 'ip_address']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Blog Post'
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return f"Anonymous ({obj.ip_address})"
    user_display.short_description = 'User'


@admin.register(BlogDislike)
class BlogDislikeAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'user_display', 'created_at']
    list_filter = ['created_at', 'post__category']
    search_fields = ['post__title', 'user__username', 'session_key', 'ip_address']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Blog Post'
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return f"Anonymous ({obj.ip_address})"
    user_display.short_description = 'User'

# Admin site customization
admin.site.site_header = "PhotoRw Blog Administration"
admin.site.site_title = "PhotoRw Blog Admin"
admin.site.index_title = "Welcome to PhotoRw Blog Administration"