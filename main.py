from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import tempfile
from PyPDF2 import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
import asyncio
from functools import lru_cache

app = FastAPI(title="PDF/EPUB Chunker", version="1.0.0")

# Добавляем CORS для лучшей совместимости
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Кэшируем text splitter для ускорения
@lru_cache(maxsize=1)
def get_text_splitter(chunk_size: int, overlap: int):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap
    )

SUPPORTED_TYPES = {
    'application/pdf': 'pdf',
    'application/epub+zip': 'epub',
    'application/octet-stream': 'epub',  # sometimes EPUB comes as octet-stream
    'application/zip': 'epub',  # some EPUB files are detected as zip
    'application/x-zip-compressed': 'epub',  # another zip variant
}

def extract_text_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка чтения PDF: {e}")

def extract_text_epub(file_path: str) -> str:
    try:
        book = epub.read_epub(file_path)
    except Exception as e:
        # Попробуем альтернативный способ для проблемных EPUB
        print(f"Ошибка при чтении EPUB: {e}")
        print("Пробуем альтернативный способ...")
        try:
            import zipfile
            text = ""
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                for file_info in zip_file.filelist:
                    if file_info.filename.endswith('.html') or file_info.filename.endswith('.xhtml'):
                        try:
                            content = zip_file.read(file_info.filename).decode('utf-8', errors='ignore')
                            soup = BeautifulSoup(content, 'html.parser')
                            text += soup.get_text(separator=' ', strip=True) + "\n"
                        except Exception as inner_e:
                            print(f"Ошибка при обработке файла {file_info.filename}: {inner_e}")
                            continue
            if not text.strip():
                raise Exception("Не удалось извлечь текст альтернативным способом")
            return text
        except Exception as alt_e:
            raise HTTPException(status_code=400, detail=f"Ошибка чтения EPUB: {e}. Альтернативный способ также не сработал: {alt_e}")
    
    text = ""
    for item in book.get_items():
        if getattr(item, 'media_type', None) == 'application/xhtml+xml':
            try:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text(separator=' ', strip=True) + "\n"
            except Exception as e:
                print(f"Ошибка при обработке элемента EPUB: {e}")
                continue
    return text

@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    chunk_size: int = Query(1000, gt=0),
    overlap: int = Query(100, ge=0)
):
    start_time = time.time()
    print(f"Получен файл: {file.filename}, тип: {file.content_type}")
    content_type = file.content_type
    file_ext = SUPPORTED_TYPES.get(content_type or "")
    
    # Если тип не определен по MIME, пробуем по расширению
    if not file_ext:
        _, ext = os.path.splitext(file.filename or "")
        ext = ext.lower()
        if ext == ".epub":
            file_ext = 'epub'
        elif ext == ".pdf":
            file_ext = 'pdf'
        else:
            print(f"Неподдерживаемый тип файла: {content_type}, расширение: {ext}")
            raise HTTPException(status_code=415, detail=f"Неподдерживаемый тип файла. Поддерживаются только PDF и EPUB файлы.")
    
    print(f"Определен тип файла: {file_ext}")

    # Ограничиваем размер файла (50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="Файл слишком большой. Максимальный размер: 50MB")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp:
        tmp.write(content)
        tmp_path = tmp.name
        print(f"Временный файл создан: {tmp_path}, размер: {len(content)} байт")

    try:
        if file_ext == 'pdf':
            print("Обрабатываем PDF файл...")
            text = extract_text_pdf(tmp_path)
        elif file_ext == 'epub':
            print("Обрабатываем EPUB файл...")
            text = extract_text_epub(tmp_path)
        else:
            raise HTTPException(status_code=415, detail="Unsupported file type")
        
        print(f"Извлечено текста: {len(text)} символов")
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        raise
    finally:
        # Удаляем временный файл
        try:
            os.remove(tmp_path)
        except:
            pass

    if not text.strip():
        print("Не удалось извлечь текст из документа")
        raise HTTPException(status_code=400, detail="No text could be extracted from the document.")

    print(f"Разбиваем текст на чанки: chunk_size={chunk_size}, overlap={overlap}")
    
    # Используем кэшированный splitter
    splitter = get_text_splitter(chunk_size, overlap)
    chunks = splitter.split_text(text)
    print(f"Создано чанков: {len(chunks)}")
    
    result_chunks = []
    for i, chunk in enumerate(chunks):
        result_chunks.append({
            "chunk_id": i + 1,
            "content": chunk
        })
    
    processing_time = time.time() - start_time
    print(f"Обработка завершена за {processing_time:.2f} секунд. Возвращаем {len(result_chunks)} чанков")
    
    return JSONResponse({
        "file_name": file.filename,
        "total_chunks": len(result_chunks),
        "processing_time": f"{processing_time:.2f}s",
        "chunks": result_chunks
    })

@app.get("/ui", response_class=HTMLResponse)
def custom_ui():
    with open("ui.html", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "PDF/EPUB Chunker"} 