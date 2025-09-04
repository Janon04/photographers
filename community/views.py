
from django.shortcuts import render, get_object_or_404
from .models import Post, CommunityCategory, ContentReport
from .forms import ContentReportForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
@login_required
def report_content(request, report_type, object_id):
	if request.method == 'POST':
		form = ContentReportForm(request.POST)
		if form.is_valid():
			report = form.save(commit=False)
			report.report_type = report_type
			report.object_id = object_id
			report.reporter = request.user
			report.save()
			messages.success(request, 'Thank you for reporting. Our team will review this content.')
			return redirect(request.META.get('HTTP_REFERER', '/'))
	else:
		form = ContentReportForm()
	return render(request, 'community/report_content.html', {'form': form, 'report_type': report_type, 'object_id': object_id})

def post_list(request):
	posts = Post.objects.all().select_related('category')
	categories = CommunityCategory.objects.all()
	return render(request, 'community/post_list.html', {'posts': posts, 'categories': categories})

def post_detail(request, pk):
	post = get_object_or_404(Post, pk=pk)
	return render(request, 'community/post_detail.html', {'post': post})
