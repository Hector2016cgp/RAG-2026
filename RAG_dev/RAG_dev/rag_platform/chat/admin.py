from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'engine_used', 'get_messages_count', 'created_at', 'is_active']
    list_filter = ['engine_used', 'is_active', 'created_at']
    search_fields = ['title', 'user__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'engine_used', 'tokens_used', 'created_at']
    list_filter = ['role', 'engine_used', 'created_at']
    search_fields = ['content', 'conversation__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
