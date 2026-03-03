"""
Procesador de documentos adaptado del código base RAG_dev
Maneja la extracción, chunking e indexación de documentos PDF/TXT
"""
import os
import re
import json
from typing import List, Dict, Optional
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document as LangChainDocument
from pypdf import PdfReader

from django.conf import settings


# Regex para extraer información estructurada
DOI_REGEX = r"10\.\d{4,9}\/[-._;()\/:A-Za-z0-9]+"
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
ORCID_REGEX = r"https?:\/\/orcid\.org\/[\d\-]{15,}"


class DocumentProcessor:
    """
    Procesador de documentos con extracción de metadata y chunking
    """
    
    def __init__(self):
        self.chunk_size = getattr(settings, 'CHUNK_SIZE', 512)
        self.chunk_overlap = getattr(settings, 'CHUNK_OVERLAP', 50)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Inicializar embedder
        self.embedder = None
    
    def get_embedder(self):
        """Lazy loading del embedder para evitar carga innecesaria"""
        if self.embedder is None:
            try:
                # Usar modelo más pequeño y estable
                model_name = getattr(settings, 'EMBEDDING_MODEL', 
                                    'sentence-transformers/all-MiniLM-L6-v2')
                self.embedder = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={
                        'device': 'cpu',
                        'trust_remote_code': False
                    },
                    encode_kwargs={
                        'normalize_embeddings': True,
                        'batch_size': 32
                    }
                )
            except Exception as e:
                print(f"Error cargando embedder: {e}")
                raise
        return self.embedder
    
    def process_document(self, file_path: str) -> Dict:
        """
        Procesa un documento PDF completo
        Retorna un diccionario con chunks, metadata y embeddings
        """
        try:
            # 1. Cargar PDF
            loader = PyMuPDFLoader(file_path)
            documents: List[LangChainDocument] = loader.load()
            
            if not documents:
                return {'error': 'No se pudo cargar el documento'}
            
            # 2. Extraer metadata
            pdf_metadata = self._extract_pdf_metadata(file_path)
            
            # 3. Extraer abstract
            full_text_first_pages = "\n\n".join(
                doc.page_content for doc in documents[:3]
            )
            abstract = self._extract_abstract(full_text_first_pages)
            
            # 4. Generar tags
            tags = self._generate_tags(
                title=pdf_metadata.get("title"),
                abstract=abstract
            )
            
            # 5. Inyectar metadata en los documentos
            for i, doc in enumerate(documents):
                doc.metadata.update(pdf_metadata)
                doc.metadata["tags"] = tags
                doc.metadata["page_number"] = doc.metadata.get("page", i) + 1
                doc.metadata["doc_id"] = file_path
                
                section = self._detect_section(doc.page_content)
                doc.metadata["section"] = section
                
                # Agregar metadata al texto (solo primera página)
                if i == 0:
                    metadata_text = []
                    if pdf_metadata.get("title"):
                        metadata_text.append(f"Título: {pdf_metadata['title']}")
                    if pdf_metadata.get("author_real"):
                        metadata_text.append(f"Autor: {pdf_metadata['author_real']}")
                    if pdf_metadata.get("year"):
                        metadata_text.append(f"Año: {pdf_metadata['year']}")
                    if pdf_metadata.get("doi"):
                        metadata_text.append(f"DOI: {pdf_metadata['doi']}")
                    
                    if metadata_text:
                        metadata_block = "\n".join(metadata_text) + "\n\n"
                        doc.page_content = metadata_block + doc.page_content
            
            # 6. Chunking
            chunked_docs: List[LangChainDocument] = self.text_splitter.split_documents(documents)
            
            # 7. Generar embeddings
            embedder = self.get_embedder()
            texts = [doc.page_content for doc in chunked_docs]
            embeddings = embedder.embed_documents(texts)
            
            # 8. Preparar resultado
            result = {
                'success': True,
                'metadata': {
                    **pdf_metadata,
                    'abstract': abstract,
                    'tags': tags,
                    'total_pages': len(documents),
                    'total_chunks': len(chunked_docs),
                },
                'chunks': [],
                'embeddings': embeddings
            }
            
            # 9. Formatear chunks
            for idx, (doc, embedding) in enumerate(zip(chunked_docs, embeddings)):
                chunk_data = {
                    'index': idx,
                    'text': doc.page_content,
                    'metadata': doc.metadata,
                    'embedding': embedding,
                    'embedding_preview': str(embedding[:5])  # Solo preview
                }
                result['chunks'].append(chunk_data)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_pdf_metadata(self, file_path: str) -> Dict:
        """Extrae metadata del PDF"""
        try:
            reader = PdfReader(file_path)
            meta = reader.metadata or {}
            
            full_first_page = reader.pages[0].extract_text() or ""
            
            # DOI
            doi_match = re.search(DOI_REGEX, full_first_page)
            doi = doi_match.group(0) if doi_match else None
            
            # ORCID
            orcids = list(set(re.findall(ORCID_REGEX, full_first_page)))
            
            # Emails
            emails = re.findall(EMAIL_REGEX, full_first_page)
            
            # Año
            year_match = re.search(r"(19|20)\d{2}", full_first_page)
            year = int(year_match.group(0)) if year_match else None
            
            # Autores
            author_real = self._guess_authors_from_first_page(full_first_page)
            
            # Título
            title = meta.get("/Title") or "Sin título"
            
            return {
                "source": file_path,
                "title": title,
                "author_real": author_real or "Autor no detectado",
                "year": year,
                "doi": doi,
                "emails": emails,
                "orcids": orcids,
            }
        except Exception:
            return {
                "source": file_path,
                "title": "Error al extraer metadata",
                "author_real": "Desconocido",
            }
    
    def _guess_authors_from_first_page(self, text: str) -> Optional[str]:
        """Detecta autores en la primera página"""
        if not text:
            return None
        
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        bad_keywords = [
            "universidad", "facultad", "coordinación", "división",
            "cd. mx", "méxico", "cuaieed", "unam", "investigación",
            "revista", "vol.", "vol ", "núm", "número", "issn",
            "departamento", "dirección general"
        ]
        
        name_pattern = re.compile(
            r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}"
        )
        
        candidates = []
        
        for line in lines:
            lower = line.lower()
            
            if len(line) > 80:
                continue
            
            if any(bad in lower for bad in bad_keywords):
                continue
            
            matches = name_pattern.findall(line)
            if matches:
                candidates.extend(matches)
        
        if candidates:
            # Tomar los primeros 3 nombres únicos
            unique_names = []
            seen = set()
            for name in candidates:
                if name not in seen and len(unique_names) < 3:
                    unique_names.append(name)
                    seen.add(name)
            
            return ", ".join(unique_names) if unique_names else None
        
        return None
    
    def _extract_abstract(self, text: str) -> str:
        """Extrae el abstract del texto"""
        if not text:
            return ""
        
        patterns = [
            r"(?i)abstract[:\s]+(.{50,800}?)(?:\n\n|keywords|introduction|1\.|resumen)",
            r"(?i)resumen[:\s]+(.{50,800}?)(?:\n\n|palabras clave|abstract|introducción)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                return " ".join(abstract.split())
        
        return ""
    
    def _generate_tags(self, title: str = None, abstract: str = None) -> List[str]:
        """Genera tags básicos del documento"""
        tags = []
        
        text = f"{title or ''} {abstract or ''}".lower()
        
        keywords_map = {
            "machine learning": ["machine learning", "ml", "aprendizaje automático"],
            "deep learning": ["deep learning", "redes neuronales", "neural network"],
            "nlp": ["nlp", "procesamiento del lenguaje natural", "natural language"],
            "computer vision": ["computer vision", "visión por computadora", "image processing"],
            "data science": ["data science", "ciencia de datos", "analytics"],
            "ai": ["artificial intelligence", "inteligencia artificial", "ai"],
        }
        
        for tag, keywords in keywords_map.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)
        
        return tags if tags else ["general"]
    
    def _detect_section(self, text: str) -> str:
        """Detecta la sección del documento"""
        text_lower = text.lower()
        
        if any(x in text_lower for x in ["abstract", "resumen"]):
            return "Resumen"
        elif any(x in text_lower for x in ["introduction", "introducción"]):
            return "Introducción"
        elif any(x in text_lower for x in ["methodology", "metodología", "materials and methods"]):
            return "Metodología"
        elif any(x in text_lower for x in ["results", "resultados"]):
            return "Resultados"
        elif any(x in text_lower for x in ["discussion", "discusión"]):
            return "Discusión"
        elif any(x in text_lower for x in ["conclusion", "conclusiones"]):
            return "Conclusiones"
        elif any(x in text_lower for x in ["references", "bibliografía", "bibliography"]):
            return "Referencias"
        else:
            return "Contenido"
