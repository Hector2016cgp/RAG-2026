from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='list'),
    path('upload/', views.document_upload, name='upload'),
    path('<int:document_id>/', views.document_detail, name='detail'),
    path('<int:document_id>/chunks/', views.document_chunks, name='chunks'),
    path('<int:document_id>/delete/', views.document_delete, name='delete'),
    path('<int:document_id>/reindex/', views.reindex_document, name='reindex'),
]
