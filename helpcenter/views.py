from django.shortcuts import render, get_object_or_404
from django.db import models
from .models import HelpCategory, HelpArticle
from config.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

def helpcenter_home(request):
    categories = HelpCategory.objects.all()
    query = request.GET.get('q', '').strip()
    faq_categories = []
    question_success = False

    if request.method == 'POST' and 'question' in request.POST:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        question = request.POST.get('question', '').strip()
        if name and email and question:
            from .models import UserQuestion
            user_question = UserQuestion.objects.create(
                name=name,
                email=email,
                question=question
            )
            
            # Send email notifications
            try:
                EmailService.send_help_question_notification(user_question)
                logger.info(f"Email notifications sent for help question #{user_question.id}")
            except Exception as e:
                logger.error(f"Failed to send email notifications for help question #{user_question.id}: {e}")
            
            question_success = True

    for category in categories:
        faqs = category.articles.filter(is_faq=True)
        if query:
            faqs = faqs.filter(title__icontains=query) | faqs.filter(content__icontains=query)
        if faqs.exists():
            faq_categories.append({'category': category, 'faqs': faqs})
    
    # Add FAQs from admin responses (UserQuestions marked as FAQ)
    from .models import UserQuestion
    user_faqs = UserQuestion.objects.filter(is_faq=True, admin_response__isnull=False).exclude(admin_response='')
    if query:
        user_faqs = user_faqs.filter(
            models.Q(question__icontains=query) | 
            models.Q(admin_response__icontains=query) |
            models.Q(faq_title__icontains=query)
        )
    
    if user_faqs.exists():
        # Group user FAQs by category
        user_faq_dict = {}
        for faq in user_faqs:
            category_name = faq.faq_category.name if faq.faq_category else "General Questions"
            if category_name not in user_faq_dict:
                user_faq_dict[category_name] = []
            user_faq_dict[category_name].append(faq)
        
        # Add to faq_categories with a special marker
        for cat_name, faqs in user_faq_dict.items():
            faq_categories.append({
                'category': {'name': cat_name}, 
                'user_faqs': faqs,
                'is_user_faq': True
            })
    return render(request, 'helpcenter/home.html', {
        'categories': categories,
        'faq_categories': faq_categories,
        'request': request,
        'question_success': question_success
    })

def helpcenter_category(request, category_id):
    category = get_object_or_404(HelpCategory, pk=category_id)
    articles = category.articles.all()
    return render(request, 'helpcenter/category.html', {'category': category, 'articles': articles})

def helpcenter_article(request, article_id):
    article = get_object_or_404(HelpArticle, pk=article_id)
    return render(request, 'helpcenter/article.html', {'article': article})
