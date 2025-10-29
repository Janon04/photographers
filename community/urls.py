from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('report/<str:report_type>/<int:object_id>/', views.report_content, name='report_content'),
]
