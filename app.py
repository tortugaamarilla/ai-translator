import streamlit as st
import os
from openai import OpenAI
from anthropic import Anthropic
import requests
import json
import base64
from PIL import Image
import io
import time
import tempfile

# Настройка страницы для мобильного отображения (должна быть первой командой Streamlit)
st.set_page_config(
    page_title="AI Переводчик | Испанский ⟷ Русский",
    page_icon="🌐",
    layout="centered",
    initial_sidebar_state="auto"
)

# Проверяем наличие прокси и удаляем его, если он установлен
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']

# Глобальная переменная для хранения последней успешно использованной модели
successful_claude_model = None

# Инициализация состояния сессии
if 'api_key_anthropic' not in st.session_state:
    st.session_state.api_key_anthropic = os.getenv('ANTHROPIC_API_KEY', '')

if 'api_key_openai' not in st.session_state:
    st.session_state.api_key_openai = os.getenv('OPENAI_API_KEY', '')

if 'api_key_elevenlabs' not in st.session_state:
    st.session_state.api_key_elevenlabs = os.getenv('ELEVENLABS_API_KEY', '')

if 'voice_id' not in st.session_state:
    st.session_state.voice_id = "2Lb1en5ujrODDIqmp7F3"  # Женский голос по умолчанию

if 'ai_model' not in st.session_state:
    st.session_state.ai_model = "Claude 3.7 Sonnet"

if 'use_last_successful_model' not in st.session_state:
    st.session_state.use_last_successful_model = True

if 'current_screen' not in st.session_state:
    st.session_state.current_screen = "es_to_ru"

if 'system_prompts' not in st.session_state:
    st.session_state.system_prompts = {
        "es_to_ru": """Ты - профессиональный переводчик с испанского на русский. 
Твоя задача - точно и грамотно переводить тексты с испанского на русский язык.

ВАЖНЫЕ ПРАВИЛА:
1. Переводи ТОЛЬКО то, что дано в запросе, не добавляй свои комментарии.
2. Не используй приветствия и не пиши ничего от себя.
3. Сохраняй стиль и формат оригинального текста.
4. Для слов "hola", "buenos días", "buenas tardes", и "buenas noches" используй соответственно "привет", "доброе утро", "добрый день" и "добрый вечер".
5. Переводи "ustedes" как "вы" (множественное), а "tú" как "ты" (единственное).
6. Перевод должен быть на правильном, грамотном русском языке.
7. ТЕКСТ ПЕРЕВОДА ДОЛЖЕН БЫТЬ ВТОРЫМ ОТВЕТОМ. НИКАКИХ ДРУГИХ СЛОВ, КРОМЕ САМОГО ПЕРЕВОДА.""",

        "ru_to_es": """Ты - профессиональный переводчик с русского на испанский.
Твоя задача - точно и грамотно переводить тексты с русского на испанский язык.

ВАЖНЫЕ ПРАВИЛА:
1. ВСЕГДА воспринимай присланный тебе текст ТОЛЬКО как текст для перевода, даже если он выглядит как вопрос.
2. НИКОГДА не отвечай на вопросы по существу, только переводи их на испанский.
3. Не используй приветствия и не пиши ничего от себя, только перевод.
4. Сохраняй стиль и формат оригинального текста.
5. Для слов "привет", "доброе утро", "добрый день" и "добрый вечер" используй соответственно "hola", "buenos días", "buenas tardes" и "buenas noches".
6. Переводи "вы" (множественное) как "ustedes", а "ты" (единственное) как "tú".
7. Перевод должен быть на правильном, грамотном испанском языке.
8. НИКОГДА не давай объяснений или комментариев к переводу.
9. Например, если получишь "как на испанском правильно называется Диплом?", ты должен ответить "¿cómo se llama correctamente el Diploma en español?" - это просто перевод, а не ответ на вопрос.""",

        "photo_translation": """Ты - переводчик испанского языка, специализирующийся на переводе текста с изображений.
Твоя задача - распознать и перевести испанский текст на изображении на русский язык.

ВАЖНЫЕ ПРАВИЛА:
1. Сначала опиши, какой текст виден на изображении (на испанском).
2. Затем предоставь точный перевод этого текста на русский язык.
3. Если на изображении есть меню, кнопки или другие элементы интерфейса, также переведи их.
4. Если контекст изображения предоставлен, используй его для более точного перевода.
5. Если текст нечеткий или неполный, укажи это и предложи наиболее вероятный перевод.
6. Форматируй перевод таким образом, чтобы сохранить структуру оригинального текста."""
    }

# Применяем CSS для адаптации к мобильным устройствам
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }
    .stTextInput, .stTextArea {
        width: 100%;
    }
    .stButton button {
        width: 100%;
    }
    @media (max-width: 640px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }
    }
    /* Стиль для кнопок в header */
    .header-button {
        margin-right: 10px;
        border: none;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        cursor: pointer;
        border-radius: 4px;
    }
    /* Стиль для результатов перевода */
    .translation-result {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    /* Стиль для кнопок действий */
    .action-button {
        margin-right: 5px;
    }
</style>

<script>
// Функция для копирования текста в буфер обмена
function copyTextToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        // Для современных браузеров
        navigator.clipboard.writeText(text).then(() => {
            console.log('Текст скопирован в буфер обмена');
        }).catch(err => {
            console.error('Ошибка при копировании текста:', err);
        });
    } else {
        // Для старых браузеров
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            console.log('Текст скопирован в буфер обмена (fallback)');
        } catch (err) {
            console.error('Ошибка при копировании текста:', err);
        }
        
        document.body.removeChild(textArea);
    }
}

// Функция для вставки текста из буфера обмена
async function pasteFromClipboard(targetId) {
    try {
        const text = await navigator.clipboard.readText();
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.value = text;
            // Вызываем событие изменения для обновления значения в streamlit
            const event = new Event('input', { bubbles: true });
            targetElement.dispatchEvent(event);
        }
    } catch (err) {
        console.error('Ошибка при вставке текста из буфера обмена:', err);
    }
}

// Настройка обработчиков событий для кнопок копирования/вставки
document.addEventListener('DOMContentLoaded', function() {
    // Прокси для обработки динамически добавляемых элементов
    document.body.addEventListener('click', function(event) {
        const target = event.target;
        
        // Проверяем, является ли цель кнопкой копирования
        if (target.closest('button') && target.textContent.includes('Копировать')) {
            // Находим ближайший блок с результатом перевода
            const resultBlock = target.closest('div').previousElementSibling.querySelector('.translation-result');
            if (resultBlock) {
                copyTextToClipboard(resultBlock.textContent);
            }
        }
        
        // Проверяем, является ли цель кнопкой вставки
        if (target.closest('button') && target.textContent.includes('📋') && !target.textContent.includes('Копировать')) {
            // Находим ближайшее текстовое поле
            const textArea = target.closest('div').previousElementSibling.querySelector('textarea');
            if (textArea) {
                pasteFromClipboard(textArea.id);
            }
        }
    });
});
</script>
""", unsafe_allow_html=True)

# Получение API ключей
try:
    # Пытаемся получить ключи из секретов, если они есть
    if 'OPENAI_API_KEY' in st.secrets:
        st.session_state.api_key_openai = st.secrets["OPENAI_API_KEY"]
    if 'ANTHROPIC_API_KEY' in st.secrets:
        st.session_state.api_key_anthropic = st.secrets["ANTHROPIC_API_KEY"]
    if 'ELEVENLABS_API_KEY' in st.secrets:
        st.session_state.api_key_elevenlabs = st.secrets["ELEVENLABS_API_KEY"]
except Exception as e:
    # Если секреты недоступны, просто продолжаем работу
    print(f"Информация: Секреты не найдены или произошла ошибка: {e}")

# Инициализация клиентов для API
def get_openai_client():
    api_key = st.session_state.api_key_openai
    if not api_key:
        st.error("API ключ OpenAI не задан")
        return None
    return OpenAI(api_key=api_key)

# Прямой вызов API Anthropic без использования официального клиента
def call_anthropic_api_directly(text, system_prompt, model_name=None):
    global successful_claude_model
    
    # Используем последнюю успешную модель, если опция выбрана и модель существует
    if st.session_state.get('use_last_successful_model', False) and st.session_state.get('last_successful_model'):
        models_to_try = [st.session_state.get('last_successful_model')]
        print(f"Используем последнюю успешную модель: {models_to_try[0]}")
    else:
        # Приоритетный список моделей для попытки
        models_to_try = [
            "claude-3-7-sonnet-20250219",  # Новая модель - приоритет
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-opus-20240229"
        ]
        # Если указана конкретная модель, пробуем её первой
        if model_name:
            if model_name not in models_to_try:
                models_to_try.insert(0, model_name)
            else:
                # Переместить указанную модель в начало списка
                models_to_try.remove(model_name)
                models_to_try.insert(0, model_name)
    
    api_key = st.session_state.api_key_anthropic
    
    if not api_key:
        return {"error": "API ключ Anthropic не задан", "response": None, "model": None}
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Отладочная информация
    debug_info = {
        "system_prompt": system_prompt,
        "user_text": text
    }
    
    for model in models_to_try:
        try:
            debug_info["model"] = model
            
            payload = {
                "model": model,
                "max_tokens": 1024,
                "temperature": 0,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": text
                    }
                ]
            }
            
            debug_info["payload"] = payload
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Сохраняем успешную модель
                successful_claude_model = model
                st.session_state['last_successful_model'] = model
                
                return {
                    "response": result["content"][0]["text"],
                    "error": None,
                    "model": model,
                    "debug_info": debug_info
                }
            else:
                error_info = f"Ошибка API ({response.status_code}): {response.text}"
                print(f"Ошибка при использовании модели {model}: {error_info}")
                # Продолжаем со следующей моделью
        except Exception as e:
            error_info = f"Исключение: {str(e)}"
            print(f"Исключение при использовании модели {model}: {error_info}")
            # Продолжаем со следующей моделью
    
    # Если ни одна модель не сработала
    return {
        "response": None,
        "error": f"Не удалось выполнить запрос ни с одной из доступных моделей Claude. Попробуйте позже или проверьте API ключ.",
        "model": None,
        "debug_info": debug_info
    }

# Функция для обработки изображения с использованием прямого вызова API
def process_image(image, context=""):
    if image is None:
        return "Изображение не предоставлено", None
    
    try:
        # Кодируем изображение в base64
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Формируем сообщение для модели
        message_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_image
                }
            }
        ]
        
        # Добавляем контекстуальную информацию, если она предоставлена
        if context and context.strip():
            message_content.append({
                "type": "text",
                "text": f"Контекст изображения: {context}"
            })
            
        # Добавляем отладочную информацию
        debug_info = {
            "system_prompt": st.session_state.system_prompts["photo_translation"],
            "has_context": bool(context and context.strip())
        }
        
        # Вызываем API
        result = call_anthropic_api_directly(
            text=message_content,
            system_prompt=st.session_state.system_prompts["photo_translation"]
        )
        
        # Обработка ошибок
        if result.get("error"):
            debug_info["error"] = result["error"]
            return f"Ошибка API: {result['error']}", debug_info
        
        # Обработка успешного ответа
        translated_text = result["response"]
        
        # Сохраняем модель в отладочную информацию
        debug_info["model_used"] = result["model"]
        
        return translated_text, debug_info
        
    except Exception as e:
        error_msg = f"Ошибка при обработке изображения: {str(e)}"
        return error_msg, {"error": error_msg}

# Функция для перевода текста с использованием выбранной модели AI
def translate_text(text, from_lang, to_lang):
    """Переводит текст с использованием API выбранной модели"""
    
    if not text or text.strip() == "":
        return "", None
    
    # Добавляем отладочную информацию
    debug_info = {}

    # Формирование текста для перевода
    if from_lang == 'es' and to_lang == 'ru':
        system_prompt = st.session_state.system_prompts["es_to_ru"]
        direction_key = 'es_to_ru'
    elif from_lang == 'ru' and to_lang == 'es':
        system_prompt = st.session_state.system_prompts["ru_to_es"]
        direction_key = 'ru_to_es'
    else:
        return f"Неподдерживаемое направление перевода: {from_lang} -> {to_lang}", None

    debug_info["direction"] = direction_key
    debug_info["system_prompt"] = system_prompt
    debug_info["input_text"] = text
    
    # Улучшенное форматирование текста для перевода
    # Заключаем текст в кавычки и явно указываем, что это текст для перевода
    formatted_text = f'Переведи следующий текст (заключённый в кавычки): "{text.strip()}"'
    
    # Выбор модели для перевода
    if st.session_state.ai_model == "Claude 3.7 Sonnet":
        try:
            # Прямой вызов API Anthropic
            result = call_anthropic_api_directly(formatted_text, system_prompt)
            
            # Обработка ошибок
            if result.get("error"):
                debug_info["error"] = result["error"]
                return f"Ошибка API: {result['error']}", debug_info
            
            # Обработка успешного ответа
            translated_text = result["response"]
            
            # Сохраняем модель в отладочную информацию
            debug_info["model_used"] = result["model"]
            
            # Удаляем кавычки, если текст начинается и заканчивается ими
            if translated_text and translated_text.startswith('"') and translated_text.endswith('"'):
                translated_text = translated_text[1:-1]
                
            return translated_text, debug_info
            
        except Exception as e:
            error_msg = f"Ошибка при переводе: {str(e)}"
            debug_info["error"] = error_msg
            return error_msg, debug_info
            
    # Другие модели будут добавлены здесь
    else:
        return f"Модель {st.session_state.ai_model} не реализована", debug_info

# Функция для озвучивания текста с помощью Elevenlabs через прямой API-запрос
def text_to_speech(text):
    if not text:
        st.warning("Нет текста для озвучивания")
        return
    
    api_key = st.session_state.api_key_elevenlabs
    if not api_key:
        st.error("Для озвучивания необходим API ключ ElevenLabs. Добавьте его в настройках.")
        return
    
    voice_id = st.session_state.voice_id
    
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        with st.spinner("Генерация аудио..."):
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Создаем временный файл для аудио
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmpfile:
                    tmpfile.write(response.content)
                    audio_path = tmpfile.name
                
                # Отображаем аудиоплеер
                st.audio(audio_path)
                
                return audio_path
            else:
                st.error(f"Ошибка при озвучивании: {response.status_code}, {response.text}")
                return None
            
    except Exception as e:
        st.error(f"Ошибка при генерации аудио: {str(e)}")
        return None

# Функция для отображения заголовка с кнопками навигации
def display_header():
    st.title("🌐 AI Переводчик | Испанский ⟷ Русский")

    # Отображение информации о модели
    if successful_claude_model:
        st.info(f"Используется модель: {successful_claude_model}")
    
    # Создаем 4 колонки для кнопок навигации
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🇪🇸 → 🇷🇺", help="Перевод с испанского на русский", use_container_width=True):
            st.session_state.current_screen = "es_to_ru"
            st.rerun()
            
    with col2:
        if st.button("🇷🇺 → 🇪🇸", help="Перевод с русского на испанский", use_container_width=True):
            st.session_state.current_screen = "ru_to_es"
            st.rerun()
            
    with col3:
        if st.button("📷 Фото", help="Перевод текста с изображения", use_container_width=True):
            st.session_state.current_screen = "photo"
            st.rerun()
            
    with col4:
        if st.button("⚙️ Настройки", help="Настройки приложения", use_container_width=True):
            st.session_state.current_screen = "settings"
            st.rerun()
            
    st.divider()

# Функция для отображения экрана перевода с испанского на русский
def display_es_to_ru():
    st.subheader("🇪🇸 → 🇷🇺 Перевод с испанского на русский")
    
    # Инициализация переменных в session_state для сохранения состояния
    if 'es_to_ru_text' not in st.session_state:
        st.session_state.es_to_ru_text = ""
    if 'es_to_ru_translation' not in st.session_state:
        st.session_state.es_to_ru_translation = None
    if 'es_to_ru_debug_info' not in st.session_state:
        st.session_state.es_to_ru_debug_info = None
    
    # Поле ввода текста на испанском
    spanish_text = st.text_area("Введите текст на испанском", height=150, key="es_ru_input", 
                              value=st.session_state.es_to_ru_text)
    
    # Сохраняем введенный текст в session_state
    st.session_state.es_to_ru_text = spanish_text
    
    # Добавляем чекбокс для отображения отладочной информации
    show_debug = st.checkbox("Показать отладочную информацию", value=False, key="show_debug_es_ru")
    
    # Шаблон запроса, который будет отправлен в API
    system_prompt = st.session_state.system_prompts["es_to_ru"]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Кнопка для перевода
        translate_button = st.button("Перевести 🔄", key="translate_es_ru")
    
    with col2:
        # Кнопка для озвучивания исходного текста
        if st.button("Озвучить исходный текст 🔊", key="speak_original_es"):
            text_to_speech(spanish_text)
    
    # Выполняем перевод при нажатии кнопки
    if spanish_text and translate_button:
        with st.spinner("Перевод..."):
            # Выполняем перевод
            translation, debug_info = translate_text(spanish_text, 'es', 'ru')
            
            # Сохраняем результаты в session_state
            st.session_state.es_to_ru_translation = translation
            st.session_state.es_to_ru_debug_info = debug_info
    
    # Отображаем результат перевода, если он есть в session_state
    if st.session_state.es_to_ru_translation:
        # Отображение результата перевода
        st.subheader("Результат перевода:")
        st.markdown(f"**{st.session_state.es_to_ru_translation}**")
        
        # Модель, которая использовалась для перевода
        if st.session_state.es_to_ru_debug_info and st.session_state.es_to_ru_debug_info.get("model_used"):
            st.info(f"Использовалась модель: {st.session_state.es_to_ru_debug_info['model_used']}")
        
        # Кнопки для действий с переводом
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📋 Копировать перевод", key="copy_es_ru"):
                st.toast("Текст скопирован в буфер обмена")
        with col2:
            if st.button("🔊 Озвучить перевод", key="speak_es_ru"):
                text_to_speech(st.session_state.es_to_ru_translation)
        
        # Отображение отладочной информации
        if show_debug and st.session_state.es_to_ru_debug_info:
            st.subheader("Отладочная информация:")
            st.json(st.session_state.es_to_ru_debug_info)
    
    # Кнопка для сброса результатов
    if st.session_state.es_to_ru_translation:
        if st.button("🔄 Новый перевод", key="new_translation_es_ru"):
            st.session_state.es_to_ru_translation = None
            st.session_state.es_to_ru_debug_info = None
            st.rerun()

# Функция для отображения экрана перевода с русского на испанский
def display_ru_to_es():
    st.subheader("🇷🇺 → 🇪🇸 Перевод с русского на испанский")
    
    # Инициализация переменных в session_state для сохранения состояния
    if 'ru_to_es_text' not in st.session_state:
        st.session_state.ru_to_es_text = ""
    if 'ru_to_es_translation' not in st.session_state:
        st.session_state.ru_to_es_translation = None
    if 'ru_to_es_debug_info' not in st.session_state:
        st.session_state.ru_to_es_debug_info = None
    
    # Поле ввода текста на русском
    russian_text = st.text_area("Введите текст на русском", height=150, key="ru_es_input", 
                               value=st.session_state.ru_to_es_text)
    
    # Сохраняем введенный текст в session_state
    st.session_state.ru_to_es_text = russian_text
    
    # Добавляем чекбокс для отображения отладочной информации
    show_debug = st.checkbox("Показать отладочную информацию", value=False, key="show_debug_ru_es")
    
    # Шаблон запроса, который будет отправлен в API
    system_prompt = st.session_state.system_prompts["ru_to_es"]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Кнопка для перевода
        translate_button = st.button("Перевести 🔄", key="translate_ru_es")
    
    # Выполняем перевод при нажатии кнопки
    if russian_text and translate_button:
        with st.spinner("Перевод..."):
            # Выполняем перевод
            translation, debug_info = translate_text(russian_text, 'ru', 'es')
            
            # Сохраняем результаты в session_state
            st.session_state.ru_to_es_translation = translation
            st.session_state.ru_to_es_debug_info = debug_info
    
    # Отображаем результат перевода, если он есть в session_state
    if st.session_state.ru_to_es_translation:
        # Отображение результата перевода
        st.subheader("Результат перевода:")
        st.markdown(f"**{st.session_state.ru_to_es_translation}**")
        
        # Модель, которая использовалась для перевода
        if st.session_state.ru_to_es_debug_info and st.session_state.ru_to_es_debug_info.get("model_used"):
            st.info(f"Использовалась модель: {st.session_state.ru_to_es_debug_info['model_used']}")
        
        # Кнопки для действий с переводом
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📋 Копировать перевод", key="copy_ru_es"):
                st.toast("Текст скопирован в буфер обмена")
        with col2:
            if st.button("🔊 Озвучить перевод", key="speak_ru_es"):
                text_to_speech(st.session_state.ru_to_es_translation)
        
        # Отображение отладочной информации
        if show_debug and st.session_state.ru_to_es_debug_info:
            st.subheader("Отладочная информация:")
            st.json(st.session_state.ru_to_es_debug_info)
    
    # Кнопка для сброса результатов
    if st.session_state.ru_to_es_translation:
        if st.button("🔄 Новый перевод", key="new_translation_ru_es"):
            st.session_state.ru_to_es_translation = None
            st.session_state.ru_to_es_debug_info = None
            st.rerun()

# Функция для отображения экрана перевода фото/скриншота
def display_photo_translation():
    st.subheader("📷 Перевод фото/скриншота")
    
    # Инициализация переменных в session_state для сохранения состояния
    if 'photo_context' not in st.session_state:
        st.session_state.photo_context = ""
    if 'photo_translation' not in st.session_state:
        st.session_state.photo_translation = None
    if 'photo_debug_info' not in st.session_state:
        st.session_state.photo_debug_info = None
    
    # Загрузка изображения
    image = st.file_uploader("Загрузите изображение с испанским текстом", type=["png", "jpg", "jpeg"], key="photo_upload")
    
    # Поле для контекста
    context = st.text_area("Контекст изображения (опционально)", value=st.session_state.photo_context, 
                           key="photo_context_input", help="Добавьте дополнительную информацию, которая поможет в переводе")
    
    # Сохраняем контекст
    st.session_state.photo_context = context
    
    # Добавляем чекбокс для отображения отладочной информации
    show_debug = st.checkbox("Показать отладочную информацию", value=False, key="show_debug_photo")
    
    if image:
        # Отображение загруженного изображения
        image_pil = Image.open(image)
        st.image(image_pil, caption="Загруженное изображение", use_column_width=True)
        
        translate_button = st.button("Перевести изображение 🔄", key="translate_photo")
        
        if translate_button:
            with st.spinner("Обработка изображения..."):
                translation, debug_info = process_image(image_pil, context)
                
                # Сохраняем результаты в session_state
                st.session_state.photo_translation = translation
                st.session_state.photo_debug_info = debug_info
    
    # Отображаем результат перевода, если он есть в session_state
    if st.session_state.photo_translation:
        # Отображение результата перевода
        st.subheader("Результат перевода:")
        st.markdown(f"**{st.session_state.photo_translation}**")
        
        # Модель, которая использовалась для перевода
        if st.session_state.photo_debug_info and st.session_state.photo_debug_info.get("model_used"):
            st.info(f"Использовалась модель: {st.session_state.photo_debug_info['model_used']}")
        
        # Кнопка для копирования перевода
        if st.button("📋 Копировать перевод", key="copy_photo"):
            st.toast("Текст скопирован в буфер обмена")
        
        # Отображение отладочной информации
        if show_debug and st.session_state.photo_debug_info:
            st.subheader("Отладочная информация:")
            st.json(st.session_state.photo_debug_info)
        
        # Кнопка для сброса результатов
        if st.button("🔄 Новый перевод", key="new_translation_photo"):
            st.session_state.photo_translation = None
            st.session_state.photo_debug_info = None
            st.rerun()

# Функция для отображения экрана настроек
def display_settings():
    global successful_claude_model
    
    st.subheader("⚙️ Настройки")
    
    # Выбор модели AI
    st.session_state.ai_model = st.selectbox(
        "Выберите модель AI для перевода:",
        ["Claude 3.7 Sonnet", "ChatGPT gpt-4o", "ChatGPT o1"],
        index=["Claude 3.7 Sonnet", "ChatGPT gpt-4o", "ChatGPT o1"].index(st.session_state.ai_model)
    )
    
    # Настройки модели Claude
    if st.session_state.ai_model == "Claude 3.7 Sonnet":
        st.subheader("Настройки модели Claude")
        
        # Отображаем текущую рабочую модель, если она есть
        if successful_claude_model:
            st.success(f"Текущая рабочая модель Claude: {successful_claude_model}")
        
        # Опция использования последней успешной модели
        st.session_state.use_last_successful_model = st.checkbox(
            "Использовать последнюю успешную модель",
            value=st.session_state.get('use_last_successful_model', False)
        )
        
        # Показываем последнюю успешную модель
        last_successful = st.session_state.get('last_successful_model', None)
        if last_successful:
            st.info(f"Последняя успешная модель: {last_successful}")
        
        # Возможность сбросить кэшированную модель
        if st.button("Сбросить кэшированную модель"):
            st.session_state['last_successful_model'] = None
            successful_claude_model = None
            st.success("Кэш модели очищен")
            st.rerun()
    
    # Выбор голоса для озвучивания
    st.subheader("Настройки голоса")
    st.session_state.voice_id = st.selectbox(
        "Выберите голос для озвучивания испанского текста:",
        [
            "Jhenny Antiques (женский)", 
            "Benjamin (мужской)"
        ],
        index=0 if st.session_state.voice_id == "2Lb1en5ujrODDIqmp7F3" else 1
    )
    
    # Обновление voice_id на основе выбора
    if st.session_state.voice_id == "Jhenny Antiques (женский)":
        st.session_state.voice_id = "2Lb1en5ujrODDIqmp7F3"
    elif st.session_state.voice_id == "Benjamin (мужской)":
        st.session_state.voice_id = "LruHrtVF6PSyGItzMNHS"
    
    # Отображение системных промптов
    st.subheader("Системные промпты")
    
    with st.expander("Перевод с испанского на русский"):
        st.text_area(
            "Системный промпт для перевода с испанского на русский:", 
            st.session_state.system_prompts["es_to_ru"],
            height=100,
            key="es_to_ru_prompt"
        )
    
    with st.expander("Перевод с русского на испанский"):
        st.text_area(
            "Системный промпт для перевода с русского на испанский:", 
            st.session_state.system_prompts["ru_to_es"],
            height=200,
            key="ru_to_es_prompt"
        )
    
    with st.expander("Перевод фото/скриншота"):
        st.text_area(
            "Системный промпт для перевода фото/скриншота:", 
            st.session_state.system_prompts["photo_translation"],
            height=300,
            key="photo_translation_prompt"
        )
    
    # Сохранение системных промптов
    if st.button("Сохранить системные промпты"):
        st.session_state.system_prompts["es_to_ru"] = st.session_state.es_to_ru_prompt
        st.session_state.system_prompts["ru_to_es"] = st.session_state.ru_to_es_prompt
        st.session_state.system_prompts["photo_translation"] = st.session_state.photo_translation_prompt
        st.success("Системные промпты сохранены!")

# Функция для отображения подвала сайта
def display_footer():
    st.divider()
    st.markdown(
        """
        <div class="footer">
            <p>AI Переводчик с испанского на русский и обратно | Версия 1.0.0</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Обновляем основную функцию для отображения меню
def main():
    # Проверка наличия API ключей
    if not st.session_state.api_key_anthropic and st.session_state.ai_model == "Claude 3.7 Sonnet":
        # Показываем форму для ввода API ключа Anthropic
        st.title("AI Переводчик | Настройка API")
        st.warning("API ключ Anthropic не найден. Введите его ниже:")
        
        api_key = st.text_input("API ключ Anthropic", type="password")
        if st.button("Сохранить API ключ"):
            if api_key:
                st.session_state.api_key_anthropic = api_key
                st.success("API ключ сохранен!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Пожалуйста, введите API ключ")
        
        # Инструкции по получению API ключа
        with st.expander("Как получить API ключ Anthropic"):
            st.markdown("""
            1. Перейдите на сайт [Anthropic](https://console.anthropic.com/)
            2. Зарегистрируйтесь или войдите в аккаунт
            3. Перейдите в раздел API Keys
            4. Создайте новый API ключ
            5. Скопируйте и вставьте его в поле выше
            """)
        
        return
    
    # Отображаем основной интерфейс, если API ключ установлен
    display_header()
    
    # Отображаем содержимое выбранной вкладки
    if st.session_state.get('current_screen', 'es_to_ru') == "es_to_ru":
        display_es_to_ru()
    elif st.session_state.get('current_screen', '') == "ru_to_es":
        display_ru_to_es()
    elif st.session_state.get('current_screen', '') == "photo":
        display_photo_translation()
    elif st.session_state.get('current_screen', '') == "settings":
        display_settings()
    
    # Отображаем footer
    display_footer()

if __name__ == "__main__":
    main() 