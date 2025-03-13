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
import random

# Настройка страницы для мобильного отображения (должна быть первой командой Streamlit)
st.set_page_config(
    page_title="AI Переводчик | Испанский ⟷ Русский",
    page_icon="🌐",
    layout="centered",
    initial_sidebar_state="auto"
)

# Базовые стили без скрытия элементов Streamlit
st.markdown('''
<style>
/* Убираем стандартные элементы управления Streamlit в правом верхнем углу */
#MainMenu {visibility: hidden !important;}
.stDeployButton {display: none !important;}
[data-testid="stToolbar"] {visibility: hidden !important;}
.viewerBadge_container__1QSob {display: none !important;}

/* Экстремальное удаление отступов для поднятия содержимого вверх */
.main .block-container {
    padding-top: 0 !important;
    padding-right: 1rem !important;
    padding-left: 1rem !important;
    max-width: 100% !important;
    margin-top: -3rem !important;
}

/* Убираем отступы у всех блоков */
.stApp > header {
    display: none !important;
}

/* Убираем отступы у текстовых полей сверху */
.stTextArea, .stTextInput {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Уменьшаем отступы у label текстовых полей */
.stTextArea label, .stTextInput label {
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
    font-size: 0.8rem !important;
    line-height: 1 !important;
}

/* Убираем все отступы у всех элементов */
div[data-testid="stVerticalBlock"] > div {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Убираем отступы у всех контейнеров */
.element-container {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* Все элементы поднимаем вверх */
.st-emotion-cache-1y4p8pa {
    padding-top: 0 !important;
    margin-top: -2rem !important;
}

/* Убираем все отступы сверху у всех возможных контейнеров */
.stApp, 
.main,
.block-container,
.css-1d391kg,
.css-18e3th9,
.css-1wyom9d,
.stApp > div:first-child,
.stApp > div > div:first-child,
.stApp > div > div > div:first-child,
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewContainer"] > div,
div[data-testid="stAppViewContainer"] > div > div,
div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* Стили для мобильных устройств */
@media only screen and (max-width: 768px) {
    .stTextInput input, .stSelectbox, .stTextArea textarea {
        width: 100% !important;
    }
    .stButton button {
        width: 100% !important;
    }
}

/* Стили для элементов перевода */
.translation-result {
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    padding: 15px;
    margin-top: 15px;
}

/* Стили для индикатора режима в правом верхнем углу */
.mode-indicator {
    position: fixed;
    top: 0.5rem;
    right: 1rem;
    padding: 0.25rem 0.75rem;
    background-color: #e8ecef;
    border-radius: 4px;
    font-size: 0.9rem;
    z-index: 1000;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

/* Стили для кнопок-ссылок */
button[data-testid*="more_variant_"], button[data-testid*="hide_variant_"] {
    background: none !important;
    color: #888 !important;
    border: none !important;
    padding: 0 !important;
    font-size: 0.8rem !important;
    text-decoration: underline !important;
    cursor: pointer !important;
    width: auto !important;
    height: auto !important;
    text-align: right !important;
    float: right !important;
    box-shadow: none !important;
    margin-bottom: 10px !important;
}
button[data-testid*="more_variant_"]:hover, button[data-testid*="hide_variant_"]:hover {
    color: #555 !important;
    background: none !important;
}
/* Скрываем тень при наведении и фокусе */
button[data-testid*="more_variant_"]:focus, button[data-testid*="hide_variant_"]:focus,
button[data-testid*="more_variant_"]:active, button[data-testid*="hide_variant_"]:active {
    box-shadow: none !important;
    outline: none !important;
}
</style>
''', unsafe_allow_html=True)

# Добавляем библиотеку Toastify для уведомлений
st.markdown("""
<link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/toastify-js/src/toastify.min.css">
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/toastify-js"></script>
""", unsafe_allow_html=True)

# Добавляем JavaScript для функций копирования и озвучивания
st.markdown("""
<script>
// Функция для копирования текста из результата перевода
function copyTranslationText(btn) {
    // Для кнопок, которые находятся под результатом перевода, ищем предыдущий элемент
    const resultDiv = btn.closest('.row-widget').parentElement.previousElementSibling.querySelector('.translation-result');
    if (resultDiv) {
        const text = resultDiv.innerText || resultDiv.textContent;
        navigator.clipboard.writeText(text)
            .then(() => {
                // Показываем уведомление
                Toastify({
                    text: "Скопировано!",
                    duration: 2000,
                    close: false,
                    gravity: "bottom",
                    position: "center",
                    stopOnFocus: true,
                    style: {
                        background: "linear-gradient(to right, #00b09b, #96c93d)",
                    }
                }).showToast();
            })
            .catch(err => {
                console.error("Ошибка при копировании: ", err);
            });
    }
}

// Функция для озвучивания текста
function speakText(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
        
        // Показываем уведомление
        Toastify({
            text: "Озвучиваю текст...",
            duration: 2000,
            close: false,
            gravity: "bottom",
            position: "center",
            stopOnFocus: true,
            style: {
                background: "linear-gradient(to right, #00b09b, #96c93d)",
            }
        }).showToast();
    } else {
        alert("Ваш браузер не поддерживает функцию озвучивания текста");
    }
}

// Функция для настройки всех кнопок копирования
function setupCopyButtons() {
    // Ищем все кнопки копирования 
    const copyButtons = document.querySelectorAll('button:has(div:contains("📋"))');
    copyButtons.forEach(button => {
        if (!button.hasAttribute('data-copy-listener')) {
            button.setAttribute('data-copy-listener', 'true');
            button.addEventListener('click', function(e) {
                copyTranslationText(this);
            });
        }
    });
}

// Функция для настройки всех кнопок озвучивания
function setupSpeakButtons() {
    // Ищем все кнопки озвучивания
    const speakButtons = document.querySelectorAll('button:has(div:contains("🔊"))');
    speakButtons.forEach(button => {
        if (!button.hasAttribute('data-speak-listener')) {
            button.setAttribute('data-speak-listener', 'true');
            button.addEventListener('click', function(e) {
                // Находим ближайший элемент перевода (теперь он находится перед кнопкой)
                const translationElement = this.closest('.row-widget').parentElement.previousElementSibling.querySelector('.translation-result');
                if (translationElement) {
                    const text = translationElement.textContent.trim();
                    if (text) {
                        speakText(text);
                    }
                }
            });
        }
    });
}

// Настраиваем MutationObserver для отслеживания добавления новых кнопок
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length) {
            setupCopyButtons();
            setupSpeakButtons();
        }
    });
});

// Наблюдаем за всеми изменениями в DOM
observer.observe(document.body, { childList: true, subtree: true });

// Вызываем функции настройки при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    setupCopyButtons();
    setupSpeakButtons();
});
</script>
""", unsafe_allow_html=True)

# Добавляем скрипт для динамического удаления отступов после загрузки страницы
st.markdown("""
<script>
// Функция для динамического удаления всех отступов сверху после загрузки страницы
document.addEventListener('DOMContentLoaded', function() {
    // Находим все контейнеры и удаляем у них отступы
    const allElements = document.querySelectorAll('div');
    allElements.forEach(el => {
        const style = window.getComputedStyle(el);
        if (parseInt(style.paddingTop) > 0 || parseInt(style.marginTop) > 0) {
            el.style.paddingTop = '0px';
            el.style.marginTop = '0px';
        }
    });
    
    // Особое внимание к первому текстовому полю - делаем отрицательный отступ
    const firstTextArea = document.querySelector('.stTextArea');
    if (firstTextArea) {
        firstTextArea.style.marginTop = '-1rem';
    }
});
</script>
""", unsafe_allow_html=True)

# Проверяем наличие прокси и удаляем его, если он установлен
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']

# Функции для работы с файлами промптов
def load_prompt_from_file(filename):
    """Загружает текст промпта из файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Ошибка при чтении файла промпта {filename}: {e}")
        return None

def save_prompt_to_file(filename, content):
    """Сохраняет текст промпта в файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        print(f"Ошибка при записи в файл промпта {filename}: {e}")
        return False

# Пути к файлам промптов
PROMPT_FILES = {
    "es_to_ru": "sys_prompt_es_to_ru.txt",
    "es_to_ru_extra": "sys_prompt_es_to_ru_extra.txt",
    "ru_to_es": "sys_prompt_ru_to_es.txt",
    "ru_to_es_one_option": "sys_prompt_ru_to_es_one_option.txt",
    "ru_to_es_several_options": "sys_prompt_ru_to_es_several_options.txt",
    "photo_translation": "sys_prompt_photo_translation.txt"
}

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

if 'use_multiple_variants' not in st.session_state:
    st.session_state.use_multiple_variants = True

# Загрузка системных промптов из файлов
if 'system_prompts' not in st.session_state:
    st.session_state.system_prompts = {}
    
    # Загружаем промпты из файлов
    for key, filename in PROMPT_FILES.items():
        prompt_text = load_prompt_from_file(filename)
        if prompt_text:
            st.session_state.system_prompts[key] = prompt_text
        else:
            st.error(f"Не удалось загрузить системный промпт из файла {filename}. Пожалуйста, проверьте наличие файла.")
            
    # Синхронизируем промпты для ru_to_es в зависимости от настроек вариантов
    if st.session_state.use_multiple_variants and "ru_to_es_several_options" in st.session_state.system_prompts:
        st.session_state.system_prompts["ru_to_es"] = st.session_state.system_prompts["ru_to_es_several_options"]
    elif "ru_to_es_one_option" in st.session_state.system_prompts:
        st.session_state.system_prompts["ru_to_es"] = st.session_state.system_prompts["ru_to_es_one_option"]

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
    /* Стиль для кнопок действий */
    .action-button {
        margin-right: 5px;
    }
</style>
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
    """
    Отправляет запрос к API Anthropic Claude с механизмом повторных попыток при перегрузке сервера.
    
    Функция реализует:
    1. Работу с несколькими моделями Claude по приоритету
    2. Логику повторных попыток с экспоненциальной задержкой при ошибке 529 (Overloaded)
    3. Визуальные индикаторы прогресса повторных попыток для пользователя
    
    Parameters:
        text (str): Текст запроса от пользователя
        system_prompt (str): Системный промпт для модели
        model_name (str, optional): Конкретная модель Claude для использования. 
                                    Если None, будет использован приоритетный список.
    
    Returns:
        dict: Словарь с ключами:
            - response: Ответ от API (str или None в случае ошибки)
            - error: Сообщение об ошибке (str или None в случае успеха)
            - model: Имя использованной модели (str или None в случае ошибки)
            - debug_info: Отладочная информация (dict)
    """
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
        # Параметры для повторных попыток с экспоненциальной задержкой
        max_retries = 5
        base_delay = 1  # начальная задержка в секундах
        retry_count = 0
        
        while retry_count <= max_retries:
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
                elif response.status_code == 529:  # Overloaded
                    # Рассчитываем задержку с учетом случайного фактора для предотвращения "грозовых вспышек"
                    delay = (base_delay * (2 ** retry_count)) + (random.randint(0, 1000) / 1000.0)
                    
                    # Ограничиваем максимальную задержку
                    if delay > 60:  # Максимальная задержка 60 секунд
                        delay = 60
                    
                    error_info = f"API перегружен (код 529). Повторная попытка через {delay:.2f} сек (попытка {retry_count+1}/{max_retries+1})"
                    print(error_info)
                    
                    # Отображаем уведомление пользователю в интерфейсе
                    retry_placeholder = st.empty()
                    retry_placeholder.warning(f"🔄 Сервер перегружен. Повторная попытка через {delay:.1f} сек (попытка {retry_count+1}/{max_retries+1})...")
                    
                    # Если это последняя попытка, показываем пользователю индикатор
                    if retry_count < max_retries:
                        time.sleep(delay)  # Ждем перед следующей попыткой
                        retry_placeholder.empty()  # Удаляем уведомление после ожидания
                        retry_count += 1
                    else:
                        # Исчерпаны все попытки для этой модели
                        retry_placeholder.error(f"⚠️ Сервер перегружен даже после {max_retries+1} попыток. Пробуем другую модель...")
                        error_info = f"Ошибка API (529): Сервис перегружен после {max_retries+1} попыток"
                        print(f"Ошибка при использовании модели {model}: {error_info}")
                        break  # Переходим к следующей модели
                else:
                    error_info = f"Ошибка API ({response.status_code}): {response.text}"
                    print(f"Ошибка при использовании модели {model}: {error_info}")
                    break  # Переходим к следующей модели при других ошибках
            except Exception as e:
                error_info = f"Исключение: {str(e)}"
                print(f"Исключение при использовании модели {model}: {error_info}")
                break  # Переходим к следующей модели при исключениях
    
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
        direction_key = 'es_to_ru'
        system_prompt = st.session_state.system_prompts["es_to_ru"]
    elif from_lang == 'ru' and to_lang == 'es':
        direction_key = 'ru_to_es'
        system_prompt = st.session_state.system_prompts["ru_to_es"]
        use_multiple_variants = st.session_state.use_multiple_variants
    else:
        return f"Неподдерживаемое направление перевода: {from_lang} -> {to_lang}", None

    debug_info["direction"] = direction_key
    debug_info["system_prompt"] = system_prompt
    debug_info["input_text"] = text
    if from_lang == 'ru' and to_lang == 'es':
        debug_info["multiple_variants"] = use_multiple_variants
    
    # Улучшенное форматирование текста для перевода
    if from_lang == 'es' and to_lang == 'ru':
        # Для испанско-русского явно указываем, что нужен только базовый перевод без деталей и примеров
        formatted_text = f'''Переведи следующий текст (заключённый в кавычки): "{text.strip()}"

ВАЖНО: Это начальный запрос, предоставь ТОЛЬКО список вариантов перевода с краткими пояснениями.
НЕ ДОБАВЛЯЙ подробные описания и примеры использования в ответ. Эта информация будет запрошена 
отдельно, только если пользователь выберет конкретный вариант.'''
    else:
        # Для других направлений используем обычный формат
        formatted_text = f'Переведи следующий текст (заключённый в кавычки): "{text.strip()}"'
    
    debug_info["formatted_text"] = formatted_text
    
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

# Функция для отображения экрана перевода с испанского на русский
def display_es_to_ru():
    # Инициализация переменных в session_state для сохранения состояния
    if 'es_to_ru_text' not in st.session_state:
        st.session_state.es_to_ru_text = ""
    if 'es_to_ru_translation' not in st.session_state:
        st.session_state.es_to_ru_translation = None
    if 'es_to_ru_debug_info' not in st.session_state:
        st.session_state.es_to_ru_debug_info = None
    if 'es_to_ru_parsed_variants' not in st.session_state:
        st.session_state.es_to_ru_parsed_variants = None
    if 'test_extra_info_result' not in st.session_state:
        st.session_state.test_extra_info_result = None
    
    # Поле ввода текста на испанском
    spanish_text = st.text_area("Введите текст на испанском", height=150, key="es_ru_input", 
                              value=st.session_state.es_to_ru_text)
    
    # Сохраняем введенный текст в session_state
    st.session_state.es_to_ru_text = spanish_text
    
    # Кнопка для перевода на всю ширину
    translate_button = st.button("Перевести", use_container_width=True, key="translate_es_ru")
    
    # Выполняем перевод при нажатии кнопки
    if spanish_text and translate_button:
        with st.spinner("Перевод..."):
            # Выполняем перевод с единым промптом
            translation, debug_info = translate_text(spanish_text, 'es', 'ru')
            
            # Сохраняем результаты в session_state
            st.session_state.es_to_ru_translation = translation
            st.session_state.es_to_ru_debug_info = debug_info
            
            # Парсим результат, чтобы выделить варианты перевода
            parsed_variants = parse_translation_variants(translation)
            st.session_state.es_to_ru_parsed_variants = parsed_variants
    
    # Проверяем, есть ли разобранные варианты перевода для короткой фразы
    if st.session_state.es_to_ru_parsed_variants and len(st.session_state.es_to_ru_parsed_variants) > 0:
        # Отображаем структурированный результат для короткой фразы/слова
        display_structured_translation(st.session_state.es_to_ru_parsed_variants, direction="es_to_ru")
        
        # Добавляем тестовую секцию для проверки API-запроса дополнительной информации
        with st.expander("🔍 Тестирование API-запроса для дополнительной информации"):
            st.info("Эта секция позволяет проверить, как работает отдельный запрос для получения дополнительной информации.")
            
            # Выбор варианта для тестирования
            variant_options = [f"{v['text']} ({v['explanation']})" for v in st.session_state.es_to_ru_parsed_variants]
            selected_variant_index = st.selectbox("Выберите вариант для тестирования:", 
                                                 range(len(variant_options)), 
                                                 format_func=lambda i: variant_options[i])
            
            if st.button("Запросить дополнительную информацию", key="test_extra_info"):
                selected_variant = st.session_state.es_to_ru_parsed_variants[selected_variant_index]
                with st.spinner("Загрузка тестовой информации..."):
                    details, examples, debug_info = get_translation_details(
                        selected_variant['text'], 
                        selected_variant['explanation']
                    )
                    
                    # Сохраняем результат теста
                    st.session_state.test_extra_info_result = {
                        "variant": selected_variant,
                        "details": details,
                        "examples": examples,
                        "debug_info": debug_info
                    }
            
            # Отображаем результат тестового запроса
            if st.session_state.test_extra_info_result:
                st.subheader("Результат тестового запроса")
                
                test_result = st.session_state.test_extra_info_result
                
                # Отображаем детали
                if test_result["details"]:
                    st.markdown("##### Подробная информация")
                    st.markdown(test_result["details"])
                
                # Отображаем примеры
                if test_result["examples"]:
                    st.markdown("##### Примеры использования")
                    st.markdown(test_result["examples"])
                
                # Отображаем отладочную информацию
                st.markdown("##### Отладочная информация")
                st.json(test_result["debug_info"])
    
    # Отображаем обычный результат перевода для предложений
    elif st.session_state.es_to_ru_translation:
        # Создаем контейнер для результата
        result_container = st.container()
        
        with result_container:
            # Отображаем результат
            st.markdown(f"""
            <div class="translation-result">
                {st.session_state.es_to_ru_translation}
            </div>
            """, unsafe_allow_html=True)
    
    # Кнопка для сброса результатов
    if st.session_state.es_to_ru_translation:
        if st.button("🔄 Новый перевод", key="new_translation_es_ru"):
            st.session_state.es_to_ru_translation = None
            st.session_state.es_to_ru_debug_info = None
            st.session_state.es_to_ru_parsed_variants = None
            st.session_state.test_extra_info_result = None
            st.session_state.es_to_ru_text = ""  # Очищаем введенный текст
            st.rerun()
    
    # Добавляем чекбокс для отображения отладочной информации В КОНЦЕ
    show_debug = st.checkbox("Показать отладочную информацию", value=False, key="show_debug_es_ru")
        
    # Отображение отладочной информации
    if show_debug and st.session_state.es_to_ru_debug_info:
        st.subheader("Отладочная информация:")
        # Добавляем информацию о количестве и составе вариантов перевода
        if st.session_state.es_to_ru_parsed_variants:
            variants_info = []
            for i, variant in enumerate(st.session_state.es_to_ru_parsed_variants):
                variant_info = {
                    "номер": i+1,
                    "текст": variant.get('text', ''),
                    "пояснение": variant.get('explanation', ''),
                    "загружены_детали": variant.get('details_loaded', False),
                    "длина_деталей": len(variant.get('details', '')),
                    "длина_примеров": len(variant.get('examples', '')),
                    "ключи": list(variant.keys())
                }
                variants_info.append(variant_info)
            
            st.session_state.es_to_ru_debug_info["variants_info"] = variants_info
        
        st.json(st.session_state.es_to_ru_debug_info)

# Функция для отображения экрана перевода с русского на испанский
def display_ru_to_es():
    # Инициализация переменных в session_state для сохранения состояния
    if 'ru_to_es_text' not in st.session_state:
        st.session_state.ru_to_es_text = ""
    if 'ru_to_es_translation' not in st.session_state:
        st.session_state.ru_to_es_translation = None
    if 'ru_to_es_debug_info' not in st.session_state:
        st.session_state.ru_to_es_debug_info = None
    if 'ru_to_es_parsed_variants' not in st.session_state:
        st.session_state.ru_to_es_parsed_variants = None
    if 'use_multiple_variants' not in st.session_state:
        st.session_state.use_multiple_variants = True
    
    # Поле ввода текста на русском
    russian_text = st.text_area("Введите текст на русском", height=150, key="ru_es_input", 
                               value=st.session_state.ru_to_es_text)
    
    # Сохраняем введенный текст в session_state
    st.session_state.ru_to_es_text = russian_text
    
    # Добавляем чекбокс для управления режимом вариантов перевода
    previous_value = st.session_state.use_multiple_variants
    st.session_state.use_multiple_variants = st.checkbox(
        "Несколько вариантов переводов", 
        value=st.session_state.use_multiple_variants,
        help="Если выбрано, то будет показано несколько вариантов перевода с комментариями и примерами для каждого варианта. Если не выбрано - только один вариант перевода без пояснений."
    )
    
    # Если значение галочки изменилось, обновляем промпт
    if previous_value != st.session_state.use_multiple_variants:
        if st.session_state.use_multiple_variants:
            st.session_state.system_prompts["ru_to_es"] = st.session_state.system_prompts["ru_to_es_several_options"]
        else:
            st.session_state.system_prompts["ru_to_es"] = st.session_state.system_prompts["ru_to_es_one_option"]
        # Обновляем промпт в файле
        save_prompt_to_file(PROMPT_FILES["ru_to_es"], st.session_state.system_prompts["ru_to_es"])
    
    # Кнопка для перевода на всю ширину
    translate_button = st.button("Перевести", use_container_width=True, key="translate_ru_es")
    
    # Выполняем перевод при нажатии кнопки
    if russian_text and translate_button:
        with st.spinner("Перевод..."):
            # Обновляем системный промпт перед переводом на основе выбранного режима
            if st.session_state.use_multiple_variants:
                st.session_state.system_prompts["ru_to_es"] = st.session_state.system_prompts["ru_to_es_several_options"]
            else:
                st.session_state.system_prompts["ru_to_es"] = st.session_state.system_prompts["ru_to_es_one_option"]
                
            # Выполняем перевод
            translation, debug_info = translate_text(russian_text, 'ru', 'es')
            
            # Сохраняем результаты в session_state
            st.session_state.ru_to_es_translation = translation
            st.session_state.ru_to_es_debug_info = debug_info
            
            # Парсим результат, чтобы выделить варианты перевода
            parsed_variants = parse_translation_variants(translation)
            st.session_state.ru_to_es_parsed_variants = parsed_variants
    
    # Проверяем, есть ли разобранные варианты перевода для короткой фразы
    if st.session_state.ru_to_es_parsed_variants and len(st.session_state.ru_to_es_parsed_variants) > 0:
        # Отображаем структурированный результат для короткой фразы/слова
        display_structured_translation(st.session_state.ru_to_es_parsed_variants, direction="ru_to_es")
    # Отображаем обычный результат перевода для предложений
    elif st.session_state.ru_to_es_translation:
        # Создаем контейнер для результата с кнопками
        result_container = st.container()
        
        with result_container:
            # Отображаем результат сначала
            st.markdown(f"""
            <div class="translation-result">
                {st.session_state.ru_to_es_translation}
            </div>
            """, unsafe_allow_html=True)
            
            # Блок с кнопками управления ПОД результатом
            action_cols = st.columns([7, 1, 1])
            with action_cols[1]:
                st.button("📋", key="copy_ru_es_inside", help="Копировать перевод")
            with action_cols[2]:
                if st.button("🔊", key="speak_ru_es_inside", help="Озвучить перевод"):
                    text_to_speech(st.session_state.ru_to_es_translation)
    
    # Кнопка для сброса результатов
    if st.session_state.ru_to_es_translation:
        if st.button("🔄 Новый перевод", key="new_translation_ru_es"):
            st.session_state.ru_to_es_translation = None
            st.session_state.ru_to_es_debug_info = None
            st.session_state.ru_to_es_parsed_variants = None
            st.session_state.ru_to_es_text = ""  # Очищаем введенный текст
            st.rerun()
    
    # Добавляем чекбокс для отображения отладочной информации В КОНЦЕ
    show_debug = st.checkbox("Показать отладочную информацию", value=False, key="show_debug_ru_es")
        
    # Отображение отладочной информации
    if show_debug and st.session_state.ru_to_es_debug_info:
        st.subheader("Отладочная информация:")
        st.json(st.session_state.ru_to_es_debug_info)

# Функция для парсинга разных вариантов перевода из ответа модели
def parse_translation_variants(translation_text):
    """
    Парсит структурированный ответ от модели и возвращает список вариантов перевода
    с их пояснениями. Подробности и примеры загружаются отдельно при необходимости.
    """
    if not translation_text:
        return []
    
    variants = []
    
    # Регулярное выражение для поиска разметки
    import re
    
    # Ищем варианты переводов с новой структурой
    variant_pattern = re.compile(r'```вариант-(\d+)\n(.*?)```', re.DOTALL)
    explanation_pattern = re.compile(r'```пояснение-(\d+)\n(.*?)```', re.DOTALL)
    
    # Проверяем, содержит ли ответ форматированные варианты
    if '```вариант-' not in translation_text:
        # Если нет форматированных вариантов, это обычный перевод предложения
        return []
    
    # Ищем все варианты перевода
    variant_matches = variant_pattern.findall(translation_text)
    
    # Если не нашли варианты в разметке - значит перевод обычного предложения, возвращаем пустой список
    if not variant_matches:
        return []
    
    # Получаем все пояснения
    explanation_matches = {num: text.strip() for num, text in explanation_pattern.findall(translation_text)}
    
    # Формируем структуру данных с вариантами
    for num, text in variant_matches:
        variant = {
            "number": num,
            "text": text.strip(),
            "explanation": explanation_matches.get(num, ""),
            "details_loaded": False  # Флаг, показывающий, что дополнительные данные не загружены
        }
        variants.append(variant)
    
    # Выводим отладочный лог о количестве найденных вариантов
    print(f"Найдено {len(variants)} вариантов перевода в исходном ответе API")
    
    return variants

# Функция для отображения структурированного перевода с вариантами
def display_structured_translation(variants, direction="es_to_ru"):
    """
    Отображает структурированный перевод с разными вариантами и пояснениями.
    Кнопка "Ещё" показывает дополнительную информацию прямо под вариантом.
    
    Parameters:
        variants: список вариантов перевода
        direction: направление перевода ("es_to_ru" или "ru_to_es")
    """
    # Добавляем CSS стили для красивого отображения вариантов перевода
    st.markdown("""
    <style>
    .variant-item {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    .variant-translation {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .variant-explanation {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }
    .details-container {
        border-left: 2px solid #ddd;
        padding-left: 10px;
        margin: 5px 0;
    }
    .example-translation {
        color: #666;
        font-style: italic;
        margin-bottom: 5px;
    }
    
    /* Стили для кнопки "Ещё" */
    .more-btn {
        margin-top: 5px !important;
        margin-bottom: 5px !important;
        padding: 0.25rem !important;
        height: auto !important;
        background-color: #f0f2f6 !important;
        color: #444 !important;
        border: none !important;
        border-radius: 4px !important;
        font-size: 0.8rem !important;
    }
    
    .more-btn:hover {
        background-color: #e0e2e6 !important;
        color: #222 !important;
    }
    
    /* Стили для мобильных устройств */
    @media only screen and (max-width: 768px) {
        .more-btn {
            width: 100% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Отображаем заголовок
    st.markdown(f"### Варианты перевода ({len(variants)})")
    
    # Инициализируем session_state для отслеживания показанных вариантов
    if 'shown_details' not in st.session_state:
        st.session_state.shown_details = {}
    
    # Отображаем каждый вариант перевода в виде карточки
    for i, variant in enumerate(variants):
        # Создаем уникальный ключ для каждого варианта
        variant_key = f"variant_{variant['number']}_{i}"
        
        # Создаем контейнер для варианта перевода
        variant_container = st.container()
        
        with variant_container:
            # Отображаем вариант перевода и его краткое пояснение
            st.markdown(f"""
            <div class="variant-item">
                <div class="variant-translation">{variant['text']}</div>
                <div class="variant-explanation">{variant['explanation']}</div>
            """, unsafe_allow_html=True)
            
            # Для испанско-русского направления добавляем возможность загрузки дополнительной информации
            if direction == "es_to_ru":
                # Проверяем, показаны ли уже детали для этого варианта
                if variant_key in st.session_state.shown_details:
                    # Если детали уже загружены, показываем их
                    details = st.session_state.shown_details[variant_key].get('details', '')
                    examples = st.session_state.shown_details[variant_key].get('examples', '')
                    
                    # Отображаем контейнер с деталями
                    st.markdown('<div class="details-container">', unsafe_allow_html=True)
                    
                    # Отображаем подробности, если они есть
                    if details:
                        st.markdown("#### Подробная информация")
                        st.markdown(details)
                    
                    # Отображаем примеры использования, если они есть
                    if examples:
                        st.markdown("#### Примеры использования")
                        
                        # Обрабатываем примеры, разделяя их на предложения и переводы
                        example_lines = examples.strip().split('\n')
                        
                        # Удаляем пустые строки и убираем маркеры списка
                        example_lines = [line[2:] if line.startswith('- ') else line for line in example_lines if line.strip()]
                        
                        # Отображаем примеры попарно (предложение + перевод)
                        example_index = 0
                        while example_index < len(example_lines):
                            if example_index + 1 < len(example_lines):
                                example = example_lines[example_index]
                                translation = example_lines[example_index + 1]
                                
                                # Используем markdown для примера на испанском
                                st.markdown(example)
                                
                                # Стилизованный перевод на русский
                                st.markdown(f"<div class='example-translation'>{translation}</div>", unsafe_allow_html=True)
                                
                                example_index += 2
                            else:
                                # Если осталась одна строка без пары
                                st.markdown(example_lines[example_index])
                                example_index += 1
                    
                    # Закрываем контейнер деталей
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Кнопка для скрытия информации
                    if st.button("Скрыть", key=f"hide_{variant_key}", help="Скрыть дополнительную информацию", use_container_width=True, 
                                type="secondary", args=None, kwargs=None, disabled=False):
                        # Удаляем вариант из показанных деталей
                        del st.session_state.shown_details[variant_key]
                        st.rerun()
                else:
                    # Если детали не загружены, показываем кнопку "Ещё"
                    more_key = f"more_{variant_key}"
                    
                    # Добавляем полноценную кнопку "Ещё"
                    if st.button("Ещё", key=more_key, help="Показать дополнительную информацию", use_container_width=True, 
                                type="secondary", args=None, kwargs=None, disabled=False):
                        with st.spinner("Загрузка дополнительной информации..."):
                            # Запрашиваем детали и примеры
                            details, examples, debug_info = get_translation_details(
                                variant['text'], 
                                variant['explanation']
                            )
                            
                            # Сохраняем данные в session_state
                            st.session_state.shown_details[variant_key] = {
                                'details': details,
                                'examples': examples,
                                'debug_info': debug_info
                            }
                            
                            # Перезагружаем страницу для отображения деталей
                            st.rerun()
            
            # Для русско-испанского направления добавляем кнопки копирования и озвучивания
            if direction == "ru_to_es":
                cols = st.columns([5, 1, 1])
                with cols[1]:
                    # Создаем уникальный ключ для кнопки копирования
                    copy_key = f"copy_{variant_key}"
                    st.button("📋", key=copy_key, help="Копировать этот вариант")
                
                with cols[2]:
                    # Создаем уникальный ключ для кнопки озвучивания
                    speak_key = f"speak_{variant_key}" 
                    if st.button("🔊", key=speak_key, help="Озвучить этот вариант"):
                        text_to_speech(variant['text'])
            
            # Закрываем div варианта
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Добавляем горизонтальную линию, кроме последнего элемента
            if i < len(variants) - 1:
                st.markdown('<hr style="margin: 10px 0; border: 0; height: 1px; background-color: #e0e0e0;">', unsafe_allow_html=True)
    
    # JavaScript для копирования текста только для русско-испанского направления
    if direction == "ru_to_es":
        st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Функция для настройки всех кнопок копирования
            function setupCopyButtons() {
                // Находим все кнопки копирования
                const copyButtons = document.querySelectorAll('button[data-testid*="copy_variant_"]');
                copyButtons.forEach(button => {
                    if (!button.hasAttribute('data-copy-listener')) {
                        button.setAttribute('data-copy-listener', 'true');
                        button.addEventListener('click', function() {
                            // Находим родительский контейнер варианта
                            const variantContainer = this.closest('.variant-item');
                            if (variantContainer) {
                                // Находим элемент с переводом
                                const translationElement = variantContainer.querySelector('.variant-translation');
                                if (translationElement) {
                                    const text = translationElement.textContent.trim();
                                    
                                    navigator.clipboard.writeText(text)
                                        .then(() => {
                                            Toastify({
                                                text: "Вариант скопирован!",
                                                duration: 2000,
                                                close: false,
                                                gravity: "bottom",
                                                position: "center",
                                                stopOnFocus: true,
                                                style: {
                                                    background: "linear-gradient(to right, #00b09b, #96c93d)",
                                                }
                                            }).showToast();
                                        })
                                        .catch(err => {
                                            console.error("Ошибка при копировании: ", err);
                                        });
                                }
                            }
                        });
                    }
                });
            }
            
            // Запускаем настройку кнопок при загрузке страницы
            setupCopyButtons();
            
            // Настраиваем MutationObserver для отслеживания добавления новых кнопок
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length) {
                        setupCopyButtons();
                    }
                });
            });
            
            // Наблюдаем за всеми изменениями в DOM
            observer.observe(document.body, { childList: true, subtree: true });
        });
        </script>
        """, unsafe_allow_html=True)
        
    # Применяем CSS для кнопок "Ещё"
    st.markdown("""
    <style>
    /* Стилизуем все кнопки "Ещё" */
    button[data-testid*="more_variant_"] {
        margin-top: 5px !important;
        margin-bottom: 5px !important;
        padding: 0.25rem !important;
        height: auto !important;
        background-color: #f0f2f6 !important;
        color: #444 !important;
        border: none !important;
        border-radius: 4px !important;
        font-size: 0.8rem !important;
    }
    
    button[data-testid*="more_variant_"]:hover {
        background-color: #e0e2e6 !important;
        color: #222 !important;
    }
    
    /* Для мобильных устройств кнопка на полную ширину */
    @media only screen and (max-width: 768px) {
        button[data-testid*="more_variant_"], button[data-testid*="hide_variant_"] {
            width: 100% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Функция для отображения экрана перевода фото/скриншота
def display_photo_translation():
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
    
    if image:
        # Отображение загруженного изображения
        image_pil = Image.open(image)
        st.image(image_pil, caption="Загруженное изображение", use_column_width=True)
        
        # Кнопка для перевода на всю ширину
        translate_button = st.button("Перевести", use_container_width=True, key="translate_photo")
        
        if translate_button:
            with st.spinner("Обработка изображения..."):
                translation, debug_info = process_image(image_pil, context)
                
                # Сохраняем результаты в session_state
                st.session_state.photo_translation = translation
                st.session_state.photo_debug_info = debug_info
    
    # Отображаем результат перевода, если он есть в session_state
    if st.session_state.photo_translation:
        # Создаем контейнер для результата с кнопками
        result_container = st.container()
        
        with result_container:
            # Отображаем результат сначала
            st.markdown(f"""
            <div class="translation-result">
                {st.session_state.photo_translation}
            </div>
            """, unsafe_allow_html=True)
            
            # Блок с кнопкой управления ПОД результатом
            action_cols = st.columns([8, 1])
            with action_cols[1]:
                st.button("📋", key="copy_photo_inside", help="Копировать перевод")
        
        # Кнопка для сброса результатов
        if st.button("🔄 Новый перевод", key="new_translation_photo"):
            st.session_state.photo_translation = None
            st.session_state.photo_debug_info = None
            st.session_state.photo_context = ""  # Очищаем поле контекста
            st.rerun()
    
    # Добавляем чекбокс для отображения отладочной информации В КОНЦЕ
    show_debug = st.checkbox("Показать отладочную информацию", value=False, key="show_debug_photo")
        
    # Отображение отладочной информации
    if show_debug and st.session_state.photo_debug_info:
        st.subheader("Отладочная информация:")
        st.json(st.session_state.photo_debug_info)

# Функция для отображения экрана настроек
def display_settings():
    global successful_claude_model
    
    # Отображаем информацию о модели
    if successful_claude_model:
        st.info(f"Используется модель: {successful_claude_model}")
    
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
    
    st.info("Системные промпты хранятся в отдельных файлах и могут быть отредактированы напрямую или через это приложение.")
    
    with st.expander("Перевод с испанского на русский"):
        es_to_ru_prompt = st.text_area(
            "Системный промпт для перевода с испанского на русский:", 
            st.session_state.system_prompts["es_to_ru"],
            height=300,
            key="es_to_ru_prompt"
        )
    
    with st.expander("Перевод с русского на испанский (один вариант)"):
        ru_to_es_one_option_prompt = st.text_area(
            "Системный промпт для перевода с русского на испанский (один вариант):", 
            st.session_state.system_prompts["ru_to_es_one_option"],
            height=200,
            key="ru_to_es_one_option_prompt"
        )
    
    with st.expander("Перевод с русского на испанский (несколько вариантов)"):
        ru_to_es_several_options_prompt = st.text_area(
            "Системный промпт для перевода с русского на испанский (несколько вариантов):", 
            st.session_state.system_prompts["ru_to_es_several_options"],
            height=200,
            key="ru_to_es_several_options_prompt"
        )
    
    with st.expander("Перевод фото/скриншота"):
        photo_translation_prompt = st.text_area(
            "Системный промпт для перевода фото/скриншота:", 
            st.session_state.system_prompts["photo_translation"],
            height=300,
            key="photo_translation_prompt"
        )
    
    # Сохранение системных промптов
    if st.button("Сохранить системные промпты"):
        # Сохраняем промпты в файлы
        success_es_to_ru = save_prompt_to_file(PROMPT_FILES["es_to_ru"], es_to_ru_prompt)
        success_ru_to_es_one = save_prompt_to_file(PROMPT_FILES["ru_to_es_one_option"], ru_to_es_one_option_prompt)
        success_ru_to_es_several = save_prompt_to_file(PROMPT_FILES["ru_to_es_several_options"], ru_to_es_several_options_prompt)
        success_photo = save_prompt_to_file(PROMPT_FILES["photo_translation"], photo_translation_prompt)
        
        if success_es_to_ru and success_ru_to_es_one and success_ru_to_es_several and success_photo:
            # Обновляем промпты в session_state
            st.session_state.system_prompts["es_to_ru"] = es_to_ru_prompt
            st.session_state.system_prompts["ru_to_es_one_option"] = ru_to_es_one_option_prompt
            st.session_state.system_prompts["ru_to_es_several_options"] = ru_to_es_several_options_prompt
            st.session_state.system_prompts["photo_translation"] = photo_translation_prompt
            
            # Обновляем текущие промпты на основе выбранного режима
            if st.session_state.use_multiple_variants:
                st.session_state.system_prompts["ru_to_es"] = st.session_state.system_prompts["ru_to_es_several_options"]
            else:
                st.session_state.system_prompts["ru_to_es"] = st.session_state.system_prompts["ru_to_es_one_option"]
            
            # Обновляем основные промптные файлы
            save_prompt_to_file(PROMPT_FILES["ru_to_es"], st.session_state.system_prompts["ru_to_es"])
            
            st.success("Системные промпты сохранены в файлы и применены в приложении!")
        else:
            st.error("Произошла ошибка при сохранении одного или нескольких промптов. Проверьте права доступа к файлам.")
    
    # Добавляем чекбокс для отображения отладочной информации В КОНЦЕ
    show_debug = st.checkbox("Показать отладочную информацию", value=False, key="show_debug_settings")
    
    # Отображение отладочной информации о текущих настройках
    if show_debug:
        debug_info = {
            "use_multiple_variants": st.session_state.use_multiple_variants,
            "current_ru_to_es_prompt_type": "several_options" if st.session_state.use_multiple_variants else "one_option",
            "prompt_files": PROMPT_FILES,
            "prompt_file_lengths": {
                key: len(st.session_state.system_prompts.get(key, "")) for key in st.session_state.system_prompts
            }
        }
        
        st.subheader("Отладочная информация о настройках:")
        st.json(debug_info)

# Функция для получения дополнительной информации о варианте перевода
def get_translation_details(word, explanation):
    """
    Запрашивает подробную информацию о конкретном варианте перевода
    
    Parameters:
        word (str): Слово или фраза на испанском
        explanation (str): Пояснение к слову или фразе из первого запроса
        
    Returns:
        tuple: (подробности, примеры, отладочная_информация)
    """
    if not word:
        return "", "", {"error": "Не указано слово для запроса дополнительной информации"}
    
    # Добавляем отладочную информацию
    debug_info = {}
    
    # Получаем системный промпт для дополнительной информации
    system_prompt = st.session_state.system_prompts["es_to_ru_extra"]
    
    # Формируем запрос к модели, явно указывая, что это повторный запрос для дополнительной информации
    formatted_text = f'''Это отдельный запрос для получения ТОЛЬКО дополнительной информации о варианте перевода.
Слово/фраза: "{word}"
Краткое пояснение: "{explanation}"

Пользователь выбрал этот вариант и хочет получить подробную информацию о нём.
'''
    
    debug_info["word"] = word
    debug_info["explanation"] = explanation
    debug_info["system_prompt"] = system_prompt
    debug_info["formatted_text"] = formatted_text
    
    try:
        # Прямой вызов API Anthropic
        result = call_anthropic_api_directly(formatted_text, system_prompt)
        
        # Обработка ошибок
        if result.get("error"):
            debug_info["error"] = result["error"]
            return "", "", debug_info
        
        # Извлекаем подробности и примеры из ответа
        response_text = result["response"]
        
        # Регулярные выражения для извлечения подробностей и примеров
        import re
        details_pattern = re.compile(r'```подробности\n(.*?)```', re.DOTALL)
        examples_pattern = re.compile(r'```примеры\n(.*?)```', re.DOTALL)
        
        # Извлекаем данные
        details_match = details_pattern.search(response_text)
        examples_match = examples_pattern.search(response_text)
        
        details = details_match.group(1).strip() if details_match else ""
        examples = examples_match.group(1).strip() if examples_match else ""
        
        # Если не удалось найти разметку, можно использовать весь ответ как подробности
        if not details and not examples and response_text.strip():
            details = response_text.strip()
        
        # Сохраняем модель в отладочную информацию
        debug_info["model_used"] = result["model"]
        debug_info["response"] = response_text
        
        # Логгируем успешное получение дополнительной информации
        print(f"Получена дополнительная информация для варианта '{word}': {len(details)} символов подробностей, {len(examples)} символов примеров")
        
        return details, examples, debug_info
        
    except Exception as e:
        error_msg = f"Ошибка при получении дополнительной информации: {str(e)}"
        debug_info["error"] = error_msg
        return "", "", debug_info

# Обновляем основную функцию для отображения приложения
def main():
    # Проверка наличия API ключей
    if not st.session_state.api_key_anthropic and st.session_state.ai_model == "Claude 3.7 Sonnet":
        # Показываем форму для ввода API ключа Anthropic в упрощенном виде
        st.markdown("""
        <div style="padding: 20px; border: 1px solid #f0f2f6; border-radius: 5px; margin-bottom: 20px;">
            <h2>AI Переводчик | Настройка API</h2>
            <p style="color: #ff4b4b; margin-bottom: 15px;">API ключ Anthropic не найден. Введите его ниже:</p>
        </div>
        """, unsafe_allow_html=True)
        
        api_key = st.text_input("API ключ Anthropic", type="password")
        
        if st.button("Сохранить API ключ", use_container_width=True):
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
    
    # Добавляем стандартное боковое меню для выбора режима
    with st.sidebar:
        st.title("AI Переводчик")
        
        # Создаем вкладки для выбора режима
        mode = st.radio(
            "Выберите режим:",
            ["🇪🇸 → 🇷🇺", 
             "🇷🇺 → 🇪🇸", 
             "📷 Фото",
             "⚙️ Настройки"]
        )
        
        # Устанавливаем текущий экран в зависимости от выбора
        if mode == "🇪🇸 → 🇷🇺":
            st.session_state.current_screen = "es_to_ru"
        elif mode == "🇷🇺 → 🇪🇸":
            st.session_state.current_screen = "ru_to_es"
        elif mode == "📷 Фото":
            st.session_state.current_screen = "photo"
        elif mode == "⚙️ Настройки":
            st.session_state.current_screen = "settings"
    
    # Определяем текст индикатора режима
    mode_indicator_text = ""
    if st.session_state.get('current_screen', 'es_to_ru') == "es_to_ru":
        mode_indicator_text = "🇪🇸 → 🇷🇺"
    elif st.session_state.get('current_screen', '') == "ru_to_es":
        mode_indicator_text = "🇷🇺 → 🇪🇸"
    elif st.session_state.get('current_screen', '') == "photo":
        mode_indicator_text = "📷 Фото"
    elif st.session_state.get('current_screen', '') == "settings":
        mode_indicator_text = "⚙️ Настройки"
    
    # Добавляем индикатор текущего режима в правый верхний угол
    st.markdown(f"""
    <div class="mode-indicator">
        {mode_indicator_text}
    </div>
    """, unsafe_allow_html=True)
    
    # Отображаем содержимое выбранной вкладки без заголовков
    if st.session_state.get('current_screen', 'es_to_ru') == "es_to_ru":
        display_es_to_ru()
    elif st.session_state.get('current_screen', '') == "ru_to_es":
        display_ru_to_es()
    elif st.session_state.get('current_screen', '') == "photo":
        display_photo_translation()
    elif st.session_state.get('current_screen', '') == "settings":
        display_settings()

if __name__ == "__main__":
    main() 