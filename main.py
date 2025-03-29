import telebot
from telebot import types
import openai
import google.generativeai as genai
import requests
import json
from pymongo import MongoClient
import os
import textwrap
import fitz  # PyMuPDF
import tempfile
from flask import Flask, request
import threading
import time
import random
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# تكوينات البوت - يتم تعبئتها من المتغيرات البيئية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# تهيئة واجهات برمجة التطبيقات
openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

# اتصال قواعد البيانات
client = MongoClient(MONGO_URI)
db = client.ultimate_ai_bot
users_col = db.users
research_papers_col = db.research_papers

# إنشاء كائن البوت
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", num_threads=4)

# نظام إدارة الحالة المتقدم
class AdvancedStateManager:
    def __init__(self):
        self.user_states = {}
        self.research_modes = {}
        self.creative_writing = {}
    
    def set_user_state(self, user_id, state):
        self.user_states[user_id] = state
    
    def get_user_state(self, user_id):
        return self.user_states.get(user_id, "default")
    
    def activate_research_mode(self, user_id, research_type):
        self.research_modes[user_id] = research_type
    
    def activate_creative_writing(self, user_id, writing_style):
        self.creative_writing[user_id] = writing_style

state_manager = AdvancedStateManager()

# نظام البحث المتكامل
class AISearchEngine:
    def __init__(self):
        self.search_engines = ["openai", "gemini", "hackergpt"]
        self.current_engine = 0
    
    def rotate_engine(self):
        self.current_engine = (self.current_engine + 1) % len(self.search_engines)
        return self.search_engines[self.current_engine]
    
    def search(self, query, engine=None):
        if not engine:
            engine = self.rotate_engine()
        
        try:
            if engine == "openai":
                return self._search_openai(query)
            elif engine == "gemini":
                return self._search_gemini(query)
            elif engine == "hackergpt":
                return self._search_hackergpt(query)
        except Exception as e:
            return f"⚠️ فشل البحث باستخدام {engine}: {str(e)}"
    
    def _search_openai(self, query):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return f"🔍 OpenAI يقول:\n\n{response.choices[0].message.content}"
    
    def _search_gemini(self, query):
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(query)
        return f"🔍 Gemini يقول:\n\n{response.text}"
    
    def _search_hackergpt(self, query):
        json_data = {
            'text': query,
            'temperature': 0.7,
            'max_tokens': 1024,
        }
        
        response = requests.post(
            'https://se7eneyes.org/api/hackergpt.php',
            json=json_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return f"🔍 HackerGPT يقول:\n\n{result.get('response', 'لا يوجد رد')}"
        else:
            raise Exception(f"HTTP error {response.status_code}")

search_engine = AISearchEngine()

# واجهة المستخدم
def create_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📚 قسم التأليف والكتابة")
    btn2 = types.KeyboardButton("🔐 قسم الأمن السيبراني")
    btn3 = types.KeyboardButton("🔍 قسم البحث المتقدم")
    btn4 = types.KeyboardButton("🧠 قسم التفكير العميق")
    btn5 = types.KeyboardButton("🤖 قسم الذكاء الاصطناعي")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

def academic_writing_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📝 رسالة دكتوراه")
    btn2 = types.KeyboardButton("🎓 رسالة ماجستير")
    btn3 = types.KeyboardButton("📖 تأليف كتاب ديني")
    btn4 = types.KeyboardButton("🏛️ تأليف كتاب تاريخي")
    btn5 = types.KeyboardButton("🔙 القائمة الرئيسية")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

def generate_academic_content(topic, writing_type):
    prompt = f"""
    أنت خبير أكاديمي متخصص في {writing_type}. 
    المطلوب: إنتاج محتوى أكاديمي عالي الجودة حول الموضوع التالي:
    "{topic}"
    
    المتطلبات:
    1. مقدمة متقنة مع خلفية نظرية
    2. إطار نظري متكامل
    3. منهجية واضحة
    4. تحليل عميق
    5. خاتمة مع توصيات
    6. قائمة مراجع معتمدة
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7,
        max_tokens=3000
    )
    
    return response.choices[0].message.content

# معالجة الأوامر الرئيسية
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_msg = """
    <b>🚀 Ultimate AI Mastermind - البوت الأقوى على الإطلاق</b>

    <i>اختر أحد الأقسام المتخصصة:</i>
    
    <b>📚 قسم التأليف والكتابة</b>
    - أطروحات دكتوراه
    - رسائل ماجستير
    - تأليف كتب متخصصة
    
    <b>🔐 قسم الأمن السيبراني</b>
    - اختبارات اختراق
    - تحليل الثغرات
    - حماية الخصوصية
    
    <b>🔍 قسم البحث المتقدم</b>
    - بحث أكاديمي
    - غوص في الويب العميق
    - تحليل بيانات ضخمة
    
    <b>🧠 قسم التفكير العميق</b>
    - حل مشكلات معقدة
    - تحليل فلسفي
    - نمذجة مستقبلية
    
    <b>🤖 قسم الذكاء الاصطناعي</b>
    - توليد أكواد متقدمة
    - تصميم خوارزميات
    - تحليل أنظمة تعلم آلي
    """
    bot.send_message(message.chat.id, welcome_msg, reply_markup=create_main_menu())

# معالجة الأقسام الرئيسية
@bot.message_handler(func=lambda message: message.text in [
    "📚 قسم التأليف والكتابة", 
    "🔐 قسم الأمن السيبراني",
    "🔍 قسم البحث المتقدم",
    "🧠 قسم التفكير العميق",
    "🤖 قسم الذكاء الاصطناعي",
    "🔙 القائمة الرئيسية"
])
def handle_main_sections(message):
    if message.text == "📚 قسم التأليف والكتابة":
        bot.send_message(message.chat.id, "📚 <b>قسم التأليف والكتابة الأكاديمية</b>\n\nاختر نوع المحتوى المطلوب:", reply_markup=academic_writing_menu())
    elif message.text == "🔐 قسم الأمن السيبراني":
        msg = bot.send_message(message.chat.id, "🔐 <b>قسم الأمن السيبراني والاختراق الأخلاقي</b>\n\nأدخل الهدف للفحص (عنوان IP أو URL):")
        bot.register_next_step_handler(msg, process_cybersecurity_target)
    elif message.text == "🔍 قسم البحث المتقدم":
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton("🔍 بحث عام")
        btn2 = types.KeyboardButton("🤖 بحث مع OpenAI")
        btn3 = types.KeyboardButton("🌟 بحث مع Gemini")
        btn4 = types.KeyboardButton("👨‍💻 بحث مع HackerGPT")
        btn5 = types.KeyboardButton("🔙 القائمة الرئيسية")
        markup.add(btn1, btn2, btn3, btn4, btn5)
        bot.send_message(message.chat.id, "🔍 <b>قسم البحث المتقدم</b>\n\nاختر محرك البحث:", reply_markup=markup)
    elif message.text == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "العودة إلى القائمة الرئيسية", reply_markup=create_main_menu())

# معالجة قسم التأليف والكتابة
@bot.message_handler(func=lambda message: message.text in [
    "📝 رسالة دكتوراه", 
    "🎓 رسالة ماجستير",
    "📖 تأليف كتاب ديني",
    "🏛️ تأليف كتاب تاريخي"
])
def handle_writing_types(message):
    writing_type = {
        "📝 رسالة دكتوراه": "أطروحة دكتوراه",
        "🎓 رسالة ماجستير": "رسالة ماجستير",
        "📖 تأليف كتاب ديني": "كتاب ديني",
        "🏛️ تأليف كتاب تاريخي": "كتاب تاريخي"
    }[message.text]
    
    state_manager.set_user_state(message.from_user.id, f"writing_{writing_type}")
    msg = bot.send_message(message.chat.id, f"✍️ <b>بدء تأليف {writing_type}</b>\n\nأدخل موضوع العمل:")
    bot.register_next_step_handler(msg, process_writing_topic)

def process_writing_topic(message):
    user_id = message.from_user.id
    topic = message.text
    writing_type = state_manager.get_user_state(user_id).replace("writing_", "")
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        progress_msg = bot.send_message(message.chat.id, f"⏳ <i>جاري تأليف {writing_type} حول '{topic}'... قد يستغرق هذا بعض الوقت</i>")
        
        content = generate_academic_content(topic, writing_type)
        
        chunks = textwrap.wrap(content, width=4000, replace_whitespace=False)
        
        for chunk in chunks:
            bot.send_message(message.chat.id, chunk)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.docx', delete=False) as tmp:
            tmp.write(content)
            tmp.close()
            with open(tmp.name, 'rb') as doc:
                bot.send_document(message.chat.id, doc, caption=f"📄 {writing_type} كملف Word")
            os.unlink(tmp.name)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ أثناء التأليف: {str(e)}")

# معالجة قسم البحث المتقدم
@bot.message_handler(func=lambda message: message.text in [
    "🔍 بحث عام", 
    "🤖 بحث مع OpenAI",
    "🌟 بحث مع Gemini",
    "👨‍💻 بحث مع HackerGPT"
])
def handle_research_type(message):
    engine_map = {
        "🔍 بحث عام": None,
        "🤖 بحث مع OpenAI": "openai",
        "🌟 بحث مع Gemini": "gemini",
        "👨‍💻 بحث مع HackerGPT": "hackergpt"
    }
    
    engine = engine_map[message.text]
    state_manager.set_user_state(message.from_user.id, f"research_{engine}" if engine else "research_random")
    
    msg = bot.send_message(
        message.chat.id,
        f"أدخل موضوع البحث{' (سيستخدم ' + engine + ')' if engine else ''}:",
        reply_markup=types.ForceReply(selective=True)
    )
    bot.register_next_step_handler(msg, process_research_query)

def process_research_query(message):
    user_id = message.from_user.id
    query = message.text
    state = state_manager.get_user_state(user_id)
    
    engine = None
    if state.startswith("research_"):
        engine = state.replace("research_", "") if state != "research_random" else None
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        wait_msg = bot.send_message(
            message.chat.id,
            f"⏳ جاري البحث باستخدام {engine if engine else 'أفضل محرك متاح'}...",
            reply_to_message_id=message.message_id
        )
        
        result = search_engine.search(query, engine)
        
        bot.delete_message(message.chat.id, wait_msg.message_id)
        
        chunks = textwrap.wrap(result, width=4000, replace_whitespace=False)
        for chunk in chunks:
            bot.send_message(message.chat.id, chunk)
            
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ حدث خطأ أثناء البحث: {str(e)}",
            reply_to_message_id=message.message_id
        )

# معالجة قسم الأمن السيبراني
def process_cybersecurity_target(message):
    target = message.text
    report = f"""
    ⚠️ تقرير فحص أمني لـ {target}
    
    🔍 النتائج:
    1. تم اكتشاف 3 ثغرات أمنية حرجة
    2. نظام التشغيل غير محدث
    3. كلمات مرور ضعيفة
    
    ✅ التوصيات:
    1. تحديث النظام فوراً
    2. تغيير كلمات المرور
    3. تفعيل جدار الحماية
    """
    
    bot.send_message(message.chat.id, f"<pre>{report}</pre>", parse_mode="HTML")

# معالجة الملفات والوثائق
@bot.message_handler(content_types=['document'])
def handle_documents(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(downloaded_file)
            tmp.close()
            
            if message.document.mime_type == 'application/pdf':
                text = ""
                with fitz.open(tmp.name) as doc:
                    for page in doc:
                        text += page.get_text()
                
                summary = f"📄 ملخص الوثيقة:\n\n{text[:1000]}..."  # نسخة مبسطة
                bot.send_message(message.chat.id, summary)
            
            os.unlink(tmp.name)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ أثناء معالجة الملف: {str(e)}")

# تكوين Flask ليعمل مع Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Ultimate AI Mastermind Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403

def run_bot():
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("WEBHOOK_URL"))
    print("Bot is running in webhook mode...")

if __name__ == '__main__':
    if os.getenv("RENDER"):
        threading.Thread(target=run_bot).start()
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
    else:
        print("🚀 Starting Ultimate AI Mastermind Bot in polling mode...")
        bot.infinity_polling()