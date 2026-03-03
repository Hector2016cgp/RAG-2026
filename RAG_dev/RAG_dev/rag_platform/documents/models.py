from django.db import models
from django.conf import settings
import os


class Document(models.Model):
    """
    Documento PDF/TXT subido por el usuario
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Usuario'
    )
    title = models.CharField(max_length=255, verbose_name='Título')
    file = models.FileField(upload_to='documents/', verbose_name='Archivo')
    file_type = models.CharField(max_length=10, verbose_name='Tipo de archivo')
    file_size = models.IntegerField(verbose_name='Tamaño (bytes)')
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    
    # Metadata extraída
    author = models.CharField(max_length=255, blank=True, verbose_name='Autor')
    year = models.IntegerField(null=True, blank=True, verbose_name='Año')
    doi = models.CharField(max_length=255, blank=True, verbose_name='DOI')
    abstract = models.TextField(blank=True, verbose_name='Resumen')
    keywords = models.TextField(blank=True, verbose_name='Palabras clave')
    
    # Procesamiento
    total_pages = models.IntegerField(null=True, blank=True, verbose_name='Total de páginas')
    total_chunks = models.IntegerField(default=0, verbose_name='Total de chunks')
    
    # Indexación
    indexed_in_faiss = models.BooleanField(default=False, verbose_name='Indexado en FAISS')
    indexed_in_neo4j = models.BooleanField(default=False, verbose_name='Indexado en Neo4j')
    faiss_index_path = models.CharField(max_length=500, blank=True, verbose_name='Ruta índice FAISS')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de subida')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de procesamiento')
    
    # Error logging
    error_message = models.TextField(blank=True, verbose_name='Mensaje de error')
    
    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_file_size_mb(self):
        """Retorna el tamaño del archivo en MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    def get_filename(self):
        """Retorna solo el nombre del archivo"""
        return os.path.basename(self.file.name)


class DocumentChunk(models.Model):
    """
    Chunk de texto extraído de un documento
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks',
        verbose_name='Documento'
    )
    chunk_id = models.CharField(max_length=255, unique=True, verbose_name='ID del chunk')
    text = models.TextField(verbose_name='Texto')
    chunk_index = models.IntegerField(verbose_name='Índice del chunk')
    
    # Metadata
    page_number = models.IntegerField(null=True, blank=True, verbose_name='Número de página')
    section = models.CharField(max_length=100, blank=True, verbose_name='Sección')
    
    # Embedding (almacenado como JSON para análisis, no para búsqueda)
    embedding_preview = models.TextField(blank=True, verbose_name='Preview del embedding')
    
    # Similitud
    similarity_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Score de similitud (última búsqueda)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    
    class Meta:
        verbose_name = 'Chunk de documento'
        verbose_name_plural = 'Chunks de documentos'
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
            models.Index(fields=['chunk_id']),
        ]
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
    
    def get_text_preview(self, max_length=100):
        """Retorna un preview del texto"""
        if len(self.text) <= max_length:
            return self.text
        return self.text[:max_length] + "..."
