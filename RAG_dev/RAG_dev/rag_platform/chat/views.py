from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Count, Q
import json

from .models import Conversation, Message
from rag_platform.documents.models import Document
from rag_platform.core.rag_engines import FaissEngine, Neo4jEngine


@login_required
def dashboard(request):
    """
    Dashboard principal del chat con historial de conversaciones
    """
    conversations = Conversation.objects.filter(
        user=request.user,
        is_active=True
    ).annotate(
        message_count=Count('messages')
    )[:20]
    
    # Estadísticas
    total_conversations = request.user.conversations.filter(is_active=True).count()
    total_messages = Message.objects.filter(conversation__user=request.user).count()
    
    # Documentos disponibles
    documents = Document.objects.filter(
        user=request.user,
        status='completed'
    )
    
    context = {
        'conversations': conversations,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'documents': documents,
        'preferred_engine': request.user.preferred_engine,
    }
    
    return render(request, 'chat/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def create_conversation(request):
    """
    Crea una nueva conversación
    """
    title = request.POST.get('title', 'Nueva Conversación')
    engine = request.POST.get('engine', request.user.preferred_engine)
    
    conversation = Conversation.objects.create(
        user=request.user,
        title=title,
        engine_used=engine
    )
    
    return JsonResponse({
        'success': True,
        'conversation_id': conversation.id,
        'title': conversation.title
    })


@login_required
def conversation_detail(request, conversation_id):
    """
    Vista detallada de una conversación con sus mensajes
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user
    )
    
    messages_list = conversation.messages.all().order_by('created_at')
    
    # Documentos para el selector
    documents = Document.objects.filter(
        user=request.user,
        status='completed'
    )
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'documents': documents,
    }
    
    return render(request, 'chat/conversation_detail.html', context)


@login_required
@require_http_methods(["POST"])
def send_message(request):
    """
    Envía un mensaje y obtiene respuesta del engine RAG.
    Soporta selección dinámica de proveedor LLM (openai/gemini/none).
    Si no hay conversation_id, crea una automáticamente.
    """
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        message_text = data.get('message')
        engine_choice = data.get('engine', 'faiss')  # faiss o neo4j
        llm_provider = data.get('llm_provider')  # openai, gemini, none, o None (usa default)
        document_id = data.get('document_id')
        
        if not message_text:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
        
        is_new_conversation = False
        
        # Si no hay conversation_id, crear una nueva
        if not conversation_id:
            # Título basado en primeras palabras del mensaje
            words = message_text.split()[:5]
            title = ' '.join(words)
            if len(title) > 40:
                title = title[:37] + '...'
            
            conversation = Conversation.objects.create(
                user=request.user,
                title=title,
                engine_used=engine_choice
            )
            is_new_conversation = True
        else:
            # Obtener conversación existente
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                user=request.user
            )
        
        # Guardar mensaje del usuario
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_text,
            engine_used=engine_choice
        )
        
        # Obtener historial (últimos 10 mensajes)
        # Nota: Django no soporta indexación negativa, usamos orden descendente y luego revertimos
        recent_messages = list(conversation.messages.all().order_by('-created_at')[:10])
        recent_messages.reverse()  # Revertir para orden cronológico
        history = [
            {
                'role': msg.role,
                'content': msg.content
            }
            for msg in recent_messages
        ]
        
        # Seleccionar engine (pasando el proveedor LLM seleccionado)
        if engine_choice == 'neo4j':
            engine = Neo4jEngine(document_id=document_id, llm_provider=llm_provider)
        else:
            engine = FaissEngine(document_id=document_id, llm_provider=llm_provider)
        
        # Generar respuesta
        response_data = engine.generate_response(
            query=message_text,
            conversation_history=history
        )
        
        # Guardar respuesta del asistente
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response_data['response'],
            engine_used=engine_choice,
            retrieval_time=response_data.get('retrieval_time'),
            generation_time=response_data.get('generation_time'),
            retrieved_chunks_count=response_data.get('retrieved_chunks', 0)
        )
        
        # Actualizar conversación
        conversation.engine_used = engine_choice
        conversation.save()
        
        # Cerrar conexión Neo4j si aplica
        if engine_choice == 'neo4j':
            engine.close()
        
        return JsonResponse({
            'success': True,
            'is_new_conversation': is_new_conversation,
            'conversation_id': conversation.id,
            'conversation_title': conversation.title,
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'created_at': user_message.created_at.isoformat()
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.content,
                'created_at': assistant_message.created_at.isoformat(),
                'engine': engine_choice,
                'llm_used': response_data.get('llm_used'),
                'retrieval_time': response_data.get('retrieval_time'),
                'generation_time': response_data.get('generation_time'),
                'chunks_info': response_data.get('chunks_info', [])
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_conversation_messages(request, conversation_id):
    """
    Obtiene los mensajes de una conversación (para cargar vía AJAX)
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user
    )
    
    messages_list = conversation.messages.all().order_by('created_at')
    
    return JsonResponse({
        'success': True,
        'conversation': {
            'id': conversation.id,
            'title': conversation.title,
            'engine': conversation.engine_used
        },
        'messages': [
            {
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'engine_used': msg.engine_used,
                'retrieval_time': msg.retrieval_time,
                'generation_time': msg.generation_time,
                'created_at': msg.created_at.isoformat()
            }
            for msg in messages_list
        ]
    })


@login_required
@require_http_methods(["POST"])
def delete_conversation(request, conversation_id):
    """
    Elimina (marca como inactiva) una conversación
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        user=request.user
    )
    
    conversation.is_active = False
    conversation.save()
    
    # Devolver JSON para peticiones AJAX
    return JsonResponse({'success': True, 'message': 'Conversación eliminada'})


@login_required
def conversation_history(request):
    """
    Lista completa del historial de conversaciones con búsqueda y filtros
    """
    from django.core.paginator import Paginator
    from django.db.models import Subquery, OuterRef
    
    search_query = request.GET.get('q', '')
    engine_filter = request.GET.get('engine', '')
    active_filter = request.GET.get('active', '')
    
    # Query base
    conversations = Conversation.objects.filter(
        user=request.user
    ).annotate(
        message_count=Count('messages')
    )
    
    # Aplicar filtros
    if search_query:
        conversations = conversations.filter(
            Q(title__icontains=search_query) |
            Q(messages__content__icontains=search_query)
        ).distinct()
    
    if engine_filter:
        conversations = conversations.filter(engine_used=engine_filter)
    
    if active_filter:
        is_active = active_filter == 'true'
        conversations = conversations.filter(is_active=is_active)
    
    # Agregar último mensaje para preview
    last_messages = Message.objects.filter(
        conversation=OuterRef('pk')
    ).order_by('-created_at').values('content')[:1]
    
    conversations = conversations.annotate(
        last_message=Subquery(last_messages)
    )
    
    conversations = conversations.order_by('-updated_at')
    
    # Estadísticas
    all_conversations = Conversation.objects.filter(user=request.user)
    total_conversations = all_conversations.count()
    faiss_count = all_conversations.filter(engine_used='faiss').count()
    neo4j_count = all_conversations.filter(engine_used='neo4j').count()
    active_count = all_conversations.filter(is_active=True).count()
    
    # Paginación
    paginator = Paginator(conversations, 10)  # 10 conversaciones por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_conversations': total_conversations,
        'faiss_count': faiss_count,
        'neo4j_count': neo4j_count,
        'active_count': active_count
    }
    
    return render(request, 'chat/conversation_history.html', context)
