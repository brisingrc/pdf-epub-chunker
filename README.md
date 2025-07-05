# 📚 Разбивка PDF/EPUB на Чанки

Веб-сервис для извлечения текста из PDF и EPUB файлов с разбивкой на чанки для дальнейшей обработки ИИ-системами.

## 🚀 Возможности

- 📄 Поддержка PDF и EPUB файлов
- ⚡ Быстрая обработка больших документов
- 🔧 Настраиваемый размер чанков и перекрытий
- 📥 Экспорт в JSON формате
- 🌐 Веб-интерфейс с drag & drop
- 🛡️ Обработка ошибок и проблемных файлов

## 🛠️ Технологии

- **Backend**: FastAPI, Python 3.11
- **Frontend**: HTML, CSS, JavaScript
- **Обработка PDF**: PyPDF2
- **Обработка EPUB**: ebooklib, BeautifulSoup
- **Разбивка текста**: LangChain

## 📦 Установка

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd <project-folder>
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите сервер:
```bash
uvicorn main:app --reload
```

4. Откройте http://127.0.0.1:8000/ui

### Docker

```bash
docker build -t pdf-epub-chunker .
docker run -p 8000:8000 pdf-epub-chunker
```

## 🌐 Деплой

### Render.com (рекомендуется)

1. Создайте аккаунт на [render.com](https://render.com)
2. Подключите ваш GitHub репозиторий
3. Создайте новый Web Service
4. Выберите репозиторий
5. Настройки:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Нажмите "Create Web Service"

### Railway.app

1. Зарегистрируйтесь на [railway.app](https://railway.app)
2. Подключите GitHub репозиторий
3. Railway автоматически определит Python проект
4. Деплой произойдет автоматически

### Heroku

1. Установите Heroku CLI
2. Создайте приложение:
```bash
heroku create your-app-name
```
3. Деплой:
```bash
git push heroku main
```

## 📖 Использование

1. Откройте веб-интерфейс
2. Перетащите PDF или EPUB файл
3. Настройте параметры:
   - Размер чанка (по умолчанию 1000 символов)
   - Перекрытие (по умолчанию 100 символов)
4. Дождитесь обработки
5. Скачайте результат в JSON формате

## 🔧 API Endpoints

- `GET /ui` - Веб-интерфейс
- `POST /upload` - Загрузка и обработка файлов
  - Параметры: `chunk_size`, `overlap`
  - Возвращает: JSON с чанками

## 📝 Пример ответа

```json
{
  "file_name": "document.pdf",
  "total_chunks": 100,
  "chunks": [
    {
      "chunk_id": 1,
      "content": "Текст чанка...",
      "start_char": 0,
      "end_char": 1000
    }
  ]
}
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License

## 🆘 Поддержка

Если у вас есть вопросы или проблемы, создайте Issue в репозитории. 