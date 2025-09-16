from django.shortcuts import render, get_object_or_404
from .models import HelpCategory, HelpArticle

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
            UserQuestion.objects.create(
                name=name,
                email=email,
                question=question
            )
            question_success = True

    for category in categories:
        faqs = category.articles.filter(is_faq=True)
        if query:
            faqs = faqs.filter(title__icontains=query) | faqs.filter(content__icontains=query)
        if faqs.exists():
            faq_categories.append({'category': category, 'faqs': faqs})
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
