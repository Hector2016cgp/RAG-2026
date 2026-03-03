from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'file_type', 'status', 'total_chunks',
        'indexed_in_faiss', 'indexed_in_neo4j', 'created_at'
    ]
    list_filter = ['status', 'file_type', 'indexed_in_faiss', 'indexed_in_neo4j', 'created_at']
    search_fields = ['title', 'author', 'doi', 'user__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('user', 'title', 'file', 'file_type', 'file_size', 'status')
        }),
        ('Metadata', {
            'fields': ('author', 'year', 'doi', 'abstract', 'keywords')
        }),
        ('Procesamiento', {
            'fields': ('total_pages', 'total_chunks', 'processed_at')
        }),
        ('Indexación', {
            'fields': ('indexed_in_faiss', 'indexed_in_neo4j', 'faiss_index_path')
        }),
        ('Errores', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['chunk_id', 'document', 'chunk_index', 'page_number', 'section', 'created_at']
    list_filter = ['document__status', 'section', 'created_at']
    search_fields = ['chunk_id', 'text', 'document__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        # Los chunks se crean automáticamente, no manualmente
        return False
