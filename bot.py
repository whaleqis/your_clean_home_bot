import os
import re
import logging

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID", "").strip()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANG, MENU, SERVICE, AREA, HOURS, NAME, PHONE, ADDRESS, CONTACT_TIME, CONTACT_HOUR = range(10)

LANGS = {
    "hy": {"name": "🇦🇲 Հայերեն", "welcome": "Ընտրեք լեզուն։"},
    "ru": {"name": "🇷🇺 Русский", "welcome": "Выберите язык."},
    "en": {"name": "🇬🇧 English", "welcome": "Choose your language."},
}

# Stable internal service IDs; only their visible labels are translated.
SERVICE_IDS = ["regular", "deep", "post", "steam", "dry", "ironing"]
T = {
"hy": {
    "welcome": "Բարի գալուստ Your Clean Home 💚🧹\n\nՄենք կօգնենք Ձեր տունը դարձնել մաքուր, թարմ ու հարմարավետ։\n\nԸնտրեք ցանկալի տարբերակը ներքևի մենյուից։",
    "menu_services": "🧹 Մեր ծառայությունները", "estimate": "💰 Մոտավոր հաշվարկել",
    "request": "📝 Ուղարկել հայտ", "call": "📞 Զանգահարել մեզ",
    "main": "⬅️ Գլխավոր մենյու", "back": "⬅️ Նախորդ քայլ",
    "change_lang": "🌐 Փոխել լեզուն",
    "services_title": "🧹 ՄԵՐ ԾԱՌԱՅՈՒԹՅՈՒՆՆԵՐԸ",
    "service_desc": "• Ընթացիկ մաքրում — տան կանոնավոր մաքրություն։\n\n• Համալիր մաքրում — տան մանրակրկիտ մաքրություն։\n\n• Հետշինարարական մաքրում — վերանորոգումից հետո մաքրություն։\n\n• Գոլորշիով մաքրում — համապատասխան մակերեսների մաքրում գոլորշու միջոցով։\n\n• Քիմմաքրում — փափուկ կահույքի և ներքնակների մաքրում։\n\n• Արդուկում — հագուստի արդուկման ծառայություն։\n\nԳինը կարող է փոխվել՝ կախված աշխատանքի ծավալից և հավելյալ ծառայություններից։",
    "choose_service_est": "Ընտրեք ծառայությունը՝ մոտավոր արժեքը հաշվարկելու համար։",
    "choose_service_req": "Լրացնենք հայտը 💚\n\nԸնտրեք Ձեզ հետաքրքրող ծառայությունը։",
    "choose_service": "Ընտրեք ծառայությունը։",
    "bad_service": "Կներեք, չհասկացա ընտրությունը 😊\nԸնտրեք ծառայություններից մեկը կոճակներով։",
    "choose_area": "Ընտրեք տարածքի մոտավոր մակերեսը կամ սեղմեք «✍️ Այլ մակերես»։",
    "other_area": "✍️ Այլ մակերես", "other_hours": "✍️ Այլ քանակ",
    "area_prompt": "Գրեք տարածքի մակերեսը քառակուսի մետրերով։ Օրինակ՝ 65։",
    "bad_area": "Ընտրեք մակերեսը կոճակներից կամ սեղմեք «✍️ Այլ մակերես»։",
    "area": "📐 Մակերես", "estimate_price": "💰 Մոտավոր հիմնական արժեք",
    "preliminary": "📌 Սա նախնական հաշվարկ է՝ առանց հավելյալ ծառայությունների։ Վերջնական արժեքը կարող է փոփոխվել՝ կախված տարածքի վիճակից և աշխատանքի ծավալից։",
    "extras_title": "➕ Հավելյալ ծառայություններ",
    "extras_regular": "• Լրացուցիչ սանհանգույց՝ 3 000 դրամ/հատ\n• Սառնարանի մաքրում՝ 3 000 դրամ\n• Պատշգամբի մաքրում՝ 2 000 դրամ\n• Արդուկում՝ 4 000 դրամ/ժամ\n• Կենդանիների առկայության դեպքում՝ 2 000 դրամ",
    "extras_deep": "• Լրացուցիչ սանհանգույց՝ 5 000 դրամ\n• Սառնարանի մաքրում՝ 3 000 դրամ\n• Պատշգամբի մաքրում՝ 3 000 դրամ\n• Դարակների մաքրում՝ 10 000 դրամ\n• Գոլորշիով մաքրում՝ 5 000 դրամ\n• Վարագույրների լվացում՝ 2 000 դրամ/հատ\n• Արդուկում՝ 4 000 դրամ/ժամ\n• Կենդանիների առկայության դեպքում՝ 4 000 դրամ",
    "extras_post": "• Դարակների մաքրում՝ 10 000 դրամ\n• Պատշգամբի մաքրում՝ 5 000 դրամ",
    "extras_steam": "Գոլորշիով մաքրման վերջնական արժեքը կախված է մակերեսից և աշխատանքի ծավալից։",
    "extras_dry": "🛋 Քիմմաքրման գներ\n\n• Բազկաթոռ՝ 2 500 դրամ\n• Երկտեղանի բազմոց՝ 8 000 դրամ\n• Եռատեղանի բազմոց՝ 10 000 դրամ\n• Երկտեղանի բազմոց + 2 բազկաթոռ՝ 10 000 դրամ\n• Եռատեղանի բազմոց + 2 բազկաթոռ՝ 12 000 դրամ\n• Անկյունային բազմոց՝ 15 000 դրամ\n• Փափուկ աթոռ՝ 2 000 դրամ\n• Փայտե աթոռ՝ 1 000 դրամ\n• Մեկտեղանի ներքնակ՝ 8 000 դրամ\n• Երկտեղանի ներքնակ՝ 12 000 դրամ\n• Մանկական ներքնակ՝ 6 000 դրամ",
    "extras_ironing": "Արդուկման արժեքը՝ 4 000 դրամ/ժամ։",
    "dry_more": "Մանրամասների համար զանգահարեք՝ 041 10 11 43, կամ սեղմեք «Ուղարկել հայտ», և մենք կզանգահարենք Ձեզ։",
    "ironing_prompt": "Արդուկման արժեքը 4 000 դրամ է մեկ ժամի համար։\nՔանի՞ ժամ է Ձեզ անհրաժեշտ։",
    "ironing_custom": "Մուտքագրեք արդուկման ժամերի քանակը։ Օրինակ՝ 5։",
    "bad_hours": "Ընտրեք ժամերի քանակը կոճակներից կամ սեղմեք «✍️ Այլ քանակ»։",
    "ironing_est": "👔 Արդուկման մոտավոր արժեք",
    "result_more": "Մանրամասների և վերջնական գինը ճշտելու համար զանգահարեք՝ 041 10 11 43, կամ սեղմեք «📝 Ուղարկել հայտ», և մենք կզանգահարենք Ձեզ։",
    "request_from_calc": "Լրացնենք հայտը 💚\n\nԾառայություն՝ {service}\nՄոտավոր արժեք՝ {price}\n\nԻնչպե՞ս դիմենք Ձեզ։ Գրեք Ձեր անունը։",
    "name_prompt": "Ինչպե՞ս դիմենք Ձեզ։ Գրեք Ձեր անունը։", "bad_name": "Կներեք, չհասկացա անունը։ Խնդրում եմ գրեք Ձեր անունը։",
    "phone_prompt": "Ուղարկեք Ձեր հեռախոսահամարը կամ ընտրեք ձեռքով մուտքագրելու տարբերակը։",
    "send_phone": "📲 Ուղարկել հեռախոսահամարս", "type_phone": "✍️ Մուտքագրել հեռախոսահամարը",
    "phone_example": "Մուտքագրեք հեռախոսահամարը, օրինակ՝ 091123456։",
    "bad_phone": "Հեռախոսահամարը կարծես ամբողջական չէ։ Փորձեք կրկին, օրինակ՝ 091123456։",
    "address_prompt": "Նշեք հասցեն կամ թաղամասը։ Եթե դեռ չգիտեք, գրեք «Կճշտեմ»։",
    "bad_address": "Խնդրում եմ նշեք հասցեն կամ թաղամասը, կամ գրեք «Կճշտեմ»։",
    "time_prompt": "📞 Ո՞ր ժամային միջակայքում է հարմար, որ կապ հաստատենք։",
    "time_any": "🕒 Ցանկացած ժամ", "time_choose": "Ընտրեք կապի հարմար ժամային միջակայքը կոճակներից։",
    "time_selected": "Ընտրել եք՝ {interval}։ Ո՞ր ժամն է Ձեզ հարմար։", "exact_time": "Ընտրեք կոնկրետ ժամը կոճակներից։",
    "thanks": "Շնորհակալություն, Ձեր հայտը ստացանք։ 💚\nՄեր թիմը կապ կհաստատի Ձեզ հետ՝ մանրամասները ճշտելու և վերջնական արժեքը ներկայացնելու համար։\nԿարող եք նաև զանգահարել՝ 041 10 11 43։",
    "send_error": "Հայտը ուղարկելիս խնդիր առաջացավ։ Խնդրում ենք զանգահարել՝ 041 10 11 43։",
    "call_text": "📞 Զանգահարեք մեզ՝ 041 10 11 43։\n\nՍիրով կպատասխանենք Ձեր հարցերին։",
    "unknown": "Կներեք, չհասկացա Ձեր հաղորդագրությունը 😊\nԽնդրում եմ ընտրեք տարբերակներից մեկը ներքևի կոճակներով։",
    "cancelled": "Գործողությունը չեղարկվեց։ Կարող եք սկսել նորից՝ /start հրամանով։",
    "service_names": ["Ընթացիկ մաքրում", "Համալիր մաքրում", "Հետշինարարական մաքրում", "Գոլորշիով մաքրում", "Քիմմաքրում", "Արդուկում"],
    "time_intervals": ["🌅 09:00–12:00", "☀️ 12:00–15:00", "🌤️ 15:00–18:00", "🌙 18:00–21:00"],
    "time_any_text": "Ցանկացած ժամ", "admin_title": "🆕 Your Clean Home — ՆՈՐ ՀԱՅՏ",
    "admin_fields": ["Անուն", "Հեռախոս", "Ծառայություն", "Մակերես / ժամեր", "Մոտավոր արժեք", "Հասցե", "Կապի հարմար ժամ", "Telegram ID"],
    "contact_error": "Չհաջողվեց ստանալ հեռախոսահամարը։ Փորձեք կրկին։"
},
"ru": {
    "welcome": "Добро пожаловать в Your Clean Home 💚🧹\n\nМы поможем сделать ваш дом чистым, свежим и уютным.\n\nВыберите нужный пункт в меню ниже.",
    "menu_services": "🧹 Наши услуги", "estimate": "💰 Рассчитать стоимость",
    "request": "📝 Оставить заявку", "call": "📞 Позвонить нам",
    "main": "⬅️ Главное меню", "back": "⬅️ Назад",
    "change_lang": "🌐 Сменить язык",
    "services_title": "🧹 НАШИ УСЛУГИ",
    "service_desc": "• Регулярная уборка — поддержание чистоты дома.\n\n• Генеральная уборка — тщательная уборка всего дома.\n\n• Уборка после ремонта — удаление строительной пыли и загрязнений.\n\n• Паровая уборка — очистка подходящих поверхностей паром.\n\n• Химчистка — чистка мягкой мебели и матрасов.\n\n• Глажка — услуга глажки одежды.\n\nЦена может меняться в зависимости от объёма работ и дополнительных услуг.",
    "choose_service_est": "Выберите услугу, чтобы рассчитать примерную стоимость.",
    "choose_service_req": "Давайте оформим заявку 💚\n\nВыберите интересующую вас услугу.",
    "choose_service": "Выберите услугу.", "bad_service": "Не удалось распознать выбор 😊\nПожалуйста, выберите услугу с помощью кнопок.",
    "choose_area": "Выберите примерную площадь или нажмите «✍️ Другая площадь».",
    "other_area": "✍️ Другая площадь", "other_hours": "✍️ Другое количество",
    "area_prompt": "Введите площадь в квадратных метрах. Например: 65.",
    "bad_area": "Выберите площадь кнопкой или нажмите «✍️ Другая площадь».",
    "area": "📐 Площадь", "estimate_price": "💰 Примерная базовая стоимость",
    "preliminary": "📌 Это предварительный расчёт без дополнительных услуг. Итоговая стоимость может измениться в зависимости от состояния помещения и объёма работ.",
    "extras_title": "➕ Дополнительные услуги",
    "extras_regular": "• Дополнительный санузел: 3 000 драм/шт.\n• Чистка холодильника: 3 000 драм\n• Уборка балкона: 2 000 драм\n• Глажка: 4 000 драм/час\n• Если есть домашние животные: 2 000 драм",
    "extras_deep": "• Дополнительный санузел: 5 000 драм\n• Чистка холодильника: 3 000 драм\n• Уборка балкона: 3 000 драм\n• Чистка шкафов и полок: 10 000 драм\n• Паровая уборка: 5 000 драм\n• Стирка штор: 2 000 драм/шт.\n• Глажка: 4 000 драм/час\n• Если есть домашние животные: 4 000 драм",
    "extras_post": "• Чистка шкафов и полок: 10 000 драм\n• Уборка балкона: 5 000 драм",
    "extras_steam": "Итоговая стоимость паровой уборки зависит от площади и объёма работ.",
    "extras_dry": "🛋 Цены на химчистку\n\n• Кресло: 2 500 драм\n• Двухместный диван: 8 000 драм\n• Трёхместный диван: 10 000 драм\n• Двухместный диван + 2 кресла: 10 000 драм\n• Трёхместный диван + 2 кресла: 12 000 драм\n• Угловой диван: 15 000 драм\n• Мягкий стул: 2 000 драм\n• Деревянный стул: 1 000 драм\n• Односпальный матрас: 8 000 драм\n• Двуспальный матрас: 12 000 драм\n• Детский матрас: 6 000 драм",
    "extras_ironing": "Стоимость глажки: 4 000 драм/час.",
    "dry_more": "Для уточнения деталей позвоните: 041 10 11 43 или нажмите «Оставить заявку», и мы вам перезвоним.",
    "ironing_prompt": "Стоимость глажки — 4 000 драм в час.\nСколько часов вам нужно?",
    "ironing_custom": "Введите количество часов глажки. Например: 5.",
    "bad_hours": "Выберите количество часов кнопкой или нажмите «✍️ Другое количество».",
    "ironing_est": "👔 Примерная стоимость глажки",
    "result_more": "Чтобы уточнить детали и итоговую стоимость, позвоните: 041 10 11 43 или нажмите «📝 Оставить заявку», и мы свяжемся с вами.",
    "request_from_calc": "Оформим заявку 💚\n\nУслуга: {service}\nПримерная стоимость: {price}\n\nКак к вам обращаться? Напишите своё имя.",
    "name_prompt": "Как к вам обращаться? Напишите своё имя.", "bad_name": "Не удалось распознать имя. Пожалуйста, введите своё имя.",
    "phone_prompt": "Отправьте номер телефона или выберите ввод вручную.",
    "send_phone": "📲 Отправить мой номер", "type_phone": "✍️ Ввести номер вручную",
    "phone_example": "Введите номер телефона, например: 091123456.",
    "bad_phone": "Похоже, номер неполный. Попробуйте ещё раз, например: 091123456.",
    "address_prompt": "Укажите адрес или район. Если пока не знаете, напишите «Уточню».",
    "bad_address": "Пожалуйста, укажите адрес или район либо напишите «Уточню».",
    "time_prompt": "📞 В какой промежуток времени вам удобно, чтобы мы связались?",
    "time_any": "🕒 В любое время", "time_choose": "Выберите удобный интервал для звонка с помощью кнопок.",
    "time_selected": "Вы выбрали: {interval}. Какое конкретно время вам удобно?", "exact_time": "Выберите конкретное время с помощью кнопок.",
    "thanks": "Спасибо! Мы получили вашу заявку. 💚\nНаша команда свяжется с вами, чтобы уточнить детали и сообщить окончательную стоимость.\nТакже можно позвонить: 041 10 11 43.",
    "send_error": "Не удалось отправить заявку. Пожалуйста, позвоните: 041 10 11 43.",
    "call_text": "📞 Позвоните нам: 041 10 11 43.\n\nБудем рады ответить на ваши вопросы.",
    "unknown": "Не удалось распознать сообщение 😊\nПожалуйста, выберите один из вариантов с помощью кнопок ниже.",
    "cancelled": "Действие отменено. Чтобы начать заново, отправьте /start.",
    "service_names": ["Регулярная уборка", "Генеральная уборка", "Уборка после ремонта", "Паровая уборка", "Химчистка", "Глажка"],
    "time_intervals": ["🌅 09:00–12:00", "☀️ 12:00–15:00", "🌤️ 15:00–18:00", "🌙 18:00–21:00"],
    "time_any_text": "В любое время", "admin_title": "🆕 Your Clean Home — НОВАЯ ЗАЯВКА",
    "admin_fields": ["Имя", "Телефон", "Услуга", "Площадь / часы", "Примерная стоимость", "Адрес", "Удобное время связи", "Telegram ID"],
    "contact_error": "Не удалось получить номер телефона. Попробуйте ещё раз."
},
"en": {
    "welcome": "Welcome to Your Clean Home 💚🧹\n\nWe’ll help make your home clean, fresh, and comfortable.\n\nChoose an option from the menu below.",
    "menu_services": "🧹 Our services", "estimate": "💰 Estimate the price",
    "request": "📝 Submit a request", "call": "📞 Call us",
    "main": "⬅️ Main menu", "back": "⬅️ Back",
    "change_lang": "🌐 Change language",
    "services_title": "🧹 OUR SERVICES",
    "service_desc": "• Regular cleaning — routine home cleaning.\n\n• Deep cleaning — a thorough clean of your home.\n\n• Post-construction cleaning — cleaning after renovation work.\n\n• Steam cleaning — steam cleaning for suitable surfaces.\n\n• Upholstery and mattress cleaning — professional furniture and mattress cleaning.\n\n• Ironing — clothing ironing service.\n\nPrices may vary depending on the scope of work and additional services.",
    "choose_service_est": "Choose a service to estimate the price.",
    "choose_service_req": "Let’s submit your request 💚\n\nChoose the service you’re interested in.",
    "choose_service": "Please choose a service.", "bad_service": "Sorry, I couldn’t understand that choice 😊\nPlease select one of the services using the buttons.",
    "choose_area": "Choose the approximate area or tap “✍️ Other area”.",
    "other_area": "✍️ Other area", "other_hours": "✍️ Other amount",
    "area_prompt": "Enter the area in square metres. For example: 65.",
    "bad_area": "Choose an area using the buttons or tap “✍️ Other area”.",
    "area": "📐 Area", "estimate_price": "💰 Estimated base price",
    "preliminary": "📌 This is a preliminary estimate and excludes additional services. The final price may vary depending on the condition of the property and the scope of work.",
    "extras_title": "➕ Additional services",
    "extras_regular": "• Additional bathroom: AMD 3,000 each\n• Fridge cleaning: AMD 3,000\n• Balcony cleaning: AMD 2,000\n• Ironing: AMD 4,000/hour\n• Pets in the home: AMD 2,000",
    "extras_deep": "• Additional bathroom: AMD 5,000\n• Fridge cleaning: AMD 3,000\n• Balcony cleaning: AMD 3,000\n• Cupboard and shelf cleaning: AMD 10,000\n• Steam cleaning: AMD 5,000\n• Curtain washing: AMD 2,000 each\n• Ironing: AMD 4,000/hour\n• Pets in the home: AMD 4,000",
    "extras_post": "• Cupboard and shelf cleaning: AMD 10,000\n• Balcony cleaning: AMD 5,000",
    "extras_steam": "The final steam-cleaning price depends on the area and scope of work.",
    "extras_dry": "🛋 Upholstery and mattress cleaning prices\n\n• Armchair: AMD 2,500\n• Two-seat sofa: AMD 8,000\n• Three-seat sofa: AMD 10,000\n• Two-seat sofa + 2 armchairs: AMD 10,000\n• Three-seat sofa + 2 armchairs: AMD 12,000\n• Corner sofa: AMD 15,000\n• Upholstered chair: AMD 2,000\n• Wooden chair: AMD 1,000\n• Single mattress: AMD 8,000\n• Double mattress: AMD 12,000\n• Child mattress: AMD 6,000",
    "extras_ironing": "Ironing costs AMD 4,000 per hour.",
    "dry_more": "For details, call 041 10 11 43 or tap “Submit a request” and we’ll call you back.",
    "ironing_prompt": "Ironing costs AMD 4,000 per hour.\nHow many hours do you need?",
    "ironing_custom": "Enter the number of ironing hours. For example: 5.",
    "bad_hours": "Choose the number of hours using the buttons or tap “✍️ Other amount”.",
    "ironing_est": "👔 Estimated ironing price",
    "result_more": "To confirm the details and final price, call 041 10 11 43 or tap “📝 Submit a request” and we’ll contact you.",
    "request_from_calc": "Let’s submit your request 💚\n\nService: {service}\nEstimated price: {price}\n\nWhat is your name?",
    "name_prompt": "What should we call you? Please enter your name.", "bad_name": "Sorry, I couldn’t read that as a name. Please enter your name.",
    "phone_prompt": "Share your phone number or choose to enter it manually.",
    "send_phone": "📲 Share my phone number", "type_phone": "✍️ Enter phone number manually",
    "phone_example": "Enter your phone number, for example: 091123456.",
    "bad_phone": "The phone number seems incomplete. Try again, for example: 091123456.",
    "address_prompt": "Enter your address or neighbourhood. If you’re not sure yet, type “I’ll confirm”.",
    "bad_address": "Please enter your address or neighbourhood, or type “I’ll confirm”.",
    "time_prompt": "📞 What time window is convenient for us to contact you?",
    "time_any": "🕒 Any time", "time_choose": "Choose a convenient time window using the buttons.",
    "time_selected": "You selected: {interval}. Which exact time works for you?", "exact_time": "Choose an exact time using the buttons.",
    "thanks": "Thank you! We’ve received your request. 💚\nOur team will contact you to confirm the details and provide the final price.\nYou can also call 041 10 11 43.",
    "send_error": "There was a problem submitting your request. Please call 041 10 11 43.",
    "call_text": "📞 Call us: 041 10 11 43.\n\nWe’ll be happy to answer your questions.",
    "unknown": "Sorry, I didn’t understand your message 😊\nPlease choose an option using the buttons below.",
    "cancelled": "Action cancelled. Send /start to begin again.",
    "service_names": ["Regular cleaning", "Deep cleaning", "Post-construction cleaning", "Steam cleaning", "Upholstery cleaning", "Ironing"],
    "time_intervals": ["🌅 09:00–12:00", "☀️ 12:00–15:00", "🌤️ 15:00–18:00", "🌙 18:00–21:00"],
    "time_any_text": "Any time", "admin_title": "🆕 Your Clean Home — NEW REQUEST",
    "admin_fields": ["Name", "Phone", "Service", "Area / hours", "Estimated price", "Address", "Preferred contact time", "Telegram ID"],
    "contact_error": "Could not receive the phone number. Please try again."
}
}

SERVICE_EXTRAS_KEY = {"regular": "extras_regular", "deep": "extras_deep", "post": "extras_post", "steam": "extras_steam", "dry": "extras_dry", "ironing": "extras_ironing"}
SERVICE_PRICES = {
    "regular": ("regular", 350, 14000),
    "deep": ("deep", 650, 26000),
    "post": ("post", 800, 32000),
}

TIME_HOURS = {
    "🌅 09:00–12:00": ["09:00", "10:00", "11:00"],
    "☀️ 12:00–15:00": ["12:00", "13:00", "14:00"],
    "🌤️ 15:00–18:00": ["15:00", "16:00", "17:00"],
    "🌙 18:00–21:00": ["18:00", "19:00", "20:00"],
}

def lang(context):
    return context.user_data.get("lang", "hy")

def tr(context, key, **kwargs):
    return T[lang(context)][key].format(**kwargs)

def service_id(context, visible):
    for i, name in enumerate(T[lang(context)]["service_names"]):
        if visible == name:
            return SERVICE_IDS[i]
    return None

def service_name(context, sid):
    return T[lang(context)]["service_names"][SERVICE_IDS.index(sid)]

def money(amount, context):
    if lang(context) == "en":
        return f"AMD {amount:,.0f}"
    if lang(context) == "ru":
        return f"{amount:,.0f} драм"
    return f"{amount:,.0f}".replace(",", " ") + " դրամ"

def main_keyboard(context):
    t = T[lang(context)]
    return ReplyKeyboardMarkup([[t["menu_services"]], [t["estimate"]], [t["request"]], [t["call"]], [t["change_lang"]]], resize_keyboard=True)

def language_keyboard():
    return ReplyKeyboardMarkup([[LANGS["hy"]["name"]], [LANGS["ru"]["name"]], [LANGS["en"]["name"]]], resize_keyboard=True)

def service_keyboard(context):
    names = T[lang(context)]["service_names"]
    t = T[lang(context)]
    return ReplyKeyboardMarkup([[names[0], names[1]], [names[2]], [names[3], names[4]], [names[5]], [t["main"]]], resize_keyboard=True)

def step_keyboard(context):
    t = T[lang(context)]
    return ReplyKeyboardMarkup([[t["back"]], [t["main"]]], resize_keyboard=True)

def phone_keyboard(context):
    t = T[lang(context)]
    return ReplyKeyboardMarkup([[KeyboardButton(t["send_phone"], request_contact=True)], [t["type_phone"]], [t["back"]], [t["main"]]], resize_keyboard=True)

def result_keyboard(context):
    t = T[lang(context)]
    return ReplyKeyboardMarkup([[t["request"]], [t["call"]], [t["estimate"]], [t["main"]]], resize_keyboard=True)

def area_keyboard(context):
    t = T[lang(context)]
    return ReplyKeyboardMarkup([["20", "30"], ["40", "50"], ["60", "70"], ["80", "100"], [t["other_area"]], [t["back"]], [t["main"]]], resize_keyboard=True)

def hours_keyboard(context):
    t = T[lang(context)]
    return ReplyKeyboardMarkup([["1", "2"], ["3", "4"], [t["other_hours"]], [t["back"]], [t["main"]]], resize_keyboard=True)

def time_keyboard(context):
    t = T[lang(context)]
    return ReplyKeyboardMarkup([[t["time_intervals"][0], t["time_intervals"][1]], [t["time_intervals"][2], t["time_intervals"][3]], [t["time_any"]], [t["back"]], [t["main"]]], resize_keyboard=True)

def exact_time_keyboard(context, interval):
    t = T[lang(context)]
    rows = [TIME_HOURS[interval][i:i+2] for i in range(0, 3, 2)]
    rows.extend([[t["back"]], [t["main"]]])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def calc(sid, area=None, hours=None):
    if sid in SERVICE_PRICES:
        _, rate, minimum = SERVICE_PRICES[sid]
        return max(minimum, area * rate)
    if sid == "steam":
        return 15000 if area < 10 else area * 1000
    if sid == "ironing":
        return hours * 4000
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text("Welcome / Բարի գալուստ / Добро пожаловать 💚\n\n" + LANGS["hy"]["welcome"], reply_markup=language_keyboard())
    return LANG

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text
    selected = next((k for k, v in LANGS.items() if text == v["name"]), None)
    if not selected:
        await update.effective_message.reply_text("Please choose a language / Խնդրում ենք ընտրել լեզուն / Пожалуйста, выберите язык.", reply_markup=language_keyboard())
        return LANG
    context.user_data.clear()
    context.user_data["lang"] = selected
    await update.effective_message.reply_text(tr(context, "welcome"), reply_markup=main_keyboard(context))
    return MENU

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Choose your language / Ընտրեք լեզուն / Выберите язык:", reply_markup=language_keyboard())
    return LANG

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(tr(context, "services_title") + "\n\n" + tr(context, "service_desc"), reply_markup=main_keyboard(context))
    return MENU

async def choose_estimate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["flow"] = "estimate"
    context.user_data.pop("service", None)
    context.user_data.pop("estimate", None)
    await update.effective_message.reply_text(tr(context, "choose_service_est"), reply_markup=service_keyboard(context))
    return SERVICE

async def start_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = T[lang(context)]
    if context.user_data.get("service") and context.user_data.get("estimate") is not None:
        context.user_data["flow"] = "request"
        await update.effective_message.reply_text(tr(context, "request_from_calc", service=service_name(context, context.user_data["service"]), price=money(context.user_data["estimate"], context)), reply_markup=step_keyboard(context))
        return NAME
    context.user_data["flow"] = "request"
    await update.effective_message.reply_text(tr(context, "choose_service_req"), reply_markup=service_keyboard(context))
    return SERVICE

async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    t = T[lang(context)]
    if text == t["main"]:
        return await start(update, context)
    sid = service_id(context, text)
    if not sid:
        await update.effective_message.reply_text(tr(context, "bad_service"), reply_markup=service_keyboard(context))
        return SERVICE
    context.user_data["service"] = sid
    if context.user_data.get("flow") == "request":
        await update.effective_message.reply_text(tr(context, "name_prompt"), reply_markup=step_keyboard(context))
        return NAME
    if sid == "dry":
        await update.effective_message.reply_text(tr(context, "extras_dry") + "\n\n" + tr(context, "dry_more"), reply_markup=result_keyboard(context))
        return MENU
    if sid == "ironing":
        await update.effective_message.reply_text(tr(context, "ironing_prompt"), reply_markup=hours_keyboard(context))
        return HOURS
    await update.effective_message.reply_text(tr(context, "choose_area"), reply_markup=area_keyboard(context))
    return AREA

async def enter_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    t = T[lang(context)]
    if text == t["main"]:
        return await start(update, context)
    if text == t["back"]:
        await update.effective_message.reply_text(tr(context, "choose_service"), reply_markup=service_keyboard(context))
        return SERVICE
    if text == t["other_area"]:
        await update.effective_message.reply_text(tr(context, "area_prompt"), reply_markup=step_keyboard(context))
        return AREA
    match = re.search(r"\d+(?:[.,]\d+)?", text)
    if not match or float(match.group().replace(",", ".")) <= 0:
        await update.effective_message.reply_text(tr(context, "bad_area"), reply_markup=area_keyboard(context))
        return AREA
    area = float(match.group().replace(",", "."))
    sid = context.user_data["service"]
    price = calc(sid, area=area)
    context.user_data["area"] = f"{area:g} m²"
    context.user_data["estimate"] = price
    extras_key = SERVICE_EXTRAS_KEY[sid]
    await update.effective_message.reply_text(
        f'{tr(context, "area")}: {area:g} m²\n{tr(context, "estimate_price")}: {money(price, context)}\n\n'
        + tr(context, "preliminary") + "\n\n" + tr(context, "extras_title") + "\n" + tr(context, extras_key)
        + "\n\n" + tr(context, "result_more"), reply_markup=result_keyboard(context))
    return MENU

async def enter_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    t = T[lang(context)]
    if text == t["main"]:
        return await start(update, context)
    if text == t["back"]:
        await update.effective_message.reply_text(tr(context, "choose_service"), reply_markup=service_keyboard(context))
        return SERVICE
    if text == t["other_hours"]:
        await update.effective_message.reply_text(tr(context, "ironing_custom"), reply_markup=step_keyboard(context))
        return HOURS
    match = re.search(r"\d+(?:[.,]\d+)?", text)
    if not match or float(match.group().replace(",", ".")) <= 0:
        await update.effective_message.reply_text(tr(context, "bad_hours"), reply_markup=hours_keyboard(context))
        return HOURS
    hours = float(match.group().replace(",", "."))
    price = calc("ironing", hours=hours)
    context.user_data["area"] = f"{hours:g} h"
    context.user_data["estimate"] = price
    await update.effective_message.reply_text(f'{tr(context, "ironing_est")}: {money(price, context)}\n\n{tr(context, "preliminary")}\n\n{tr(context, "result_more")}', reply_markup=result_keyboard(context))
    return MENU

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    t = T[lang(context)]
    if text == t["main"]:
        return await start(update, context)
    if text == t["back"]:
        await update.effective_message.reply_text(tr(context, "choose_service"), reply_markup=service_keyboard(context))
        return SERVICE
    if len(text) < 2:
        await update.effective_message.reply_text(tr(context, "bad_name"), reply_markup=step_keyboard(context))
        return NAME
    context.user_data["name"] = text
    await update.effective_message.reply_text(tr(context, "phone_prompt"), reply_markup=phone_keyboard(context))
    return PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    t = T[lang(context)]
    if text == t["main"]:
        return await start(update, context)
    if text == t["back"]:
        await update.effective_message.reply_text(tr(context, "name_prompt"), reply_markup=step_keyboard(context))
        return NAME
    if text == t["type_phone"]:
        await update.effective_message.reply_text(tr(context, "phone_example"), reply_markup=step_keyboard(context))
        return PHONE
    normalized = "".join(ch for ch in text if ch.isdigit() or ch == "+")
    if len("".join(ch for ch in normalized if ch.isdigit())) < 8:
        await update.effective_message.reply_text(tr(context, "bad_phone"), reply_markup=phone_keyboard(context))
        return PHONE
    context.user_data["phone"] = normalized
    await update.effective_message.reply_text(tr(context, "address_prompt"), reply_markup=step_keyboard(context))
    return ADDRESS

async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.effective_message.contact
    if not contact or not contact.phone_number:
        await update.effective_message.reply_text(tr(context, "contact_error"), reply_markup=phone_keyboard(context))
        return PHONE
    context.user_data["phone"] = contact.phone_number
    await update.effective_message.reply_text(tr(context, "address_prompt"), reply_markup=step_keyboard(context))
    return ADDRESS

async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    t = T[lang(context)]
    if text == t["main"]:
        return await start(update, context)
    if text == t["back"]:
        await update.effective_message.reply_text(tr(context, "phone_prompt"), reply_markup=phone_keyboard(context))
        return PHONE
    if not text:
        await update.effective_message.reply_text(tr(context, "bad_address"), reply_markup=step_keyboard(context))
        return ADDRESS
    context.user_data["address"] = text
    await update.effective_message.reply_text(tr(context, "time_prompt"), reply_markup=time_keyboard(context))
    return CONTACT_TIME

async def enter_contact_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    t = T[lang(context)]
    if text == t["main"]:
        return await start(update, context)
    if text == t["back"]:
        await update.effective_message.reply_text(tr(context, "address_prompt"), reply_markup=step_keyboard(context))
        return ADDRESS
    if text == t["time_any"]:
        context.user_data["contact_time"] = t["time_any_text"]
        return await finish_lead(update, context)
    if text not in t["time_intervals"]:
        await update.effective_message.reply_text(tr(context, "time_choose"), reply_markup=time_keyboard(context))
        return CONTACT_TIME
    # The labels are the same in all three languages; map by position for robust lookup.
    idx = t["time_intervals"].index(text)
    interval = list(TIME_HOURS.keys())[idx]
    context.user_data["contact_interval"] = interval
    await update.effective_message.reply_text(tr(context, "time_selected", interval=text), reply_markup=exact_time_keyboard(context, interval))
    return CONTACT_HOUR

async def enter_contact_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    t = T[lang(context)]
    if text == t["main"]:
        return await start(update, context)
    if text == t["back"]:
        await update.effective_message.reply_text(tr(context, "time_prompt"), reply_markup=time_keyboard(context))
        return CONTACT_TIME
    interval = context.user_data.get("contact_interval")
    if interval not in TIME_HOURS or text not in TIME_HOURS[interval]:
        await update.effective_message.reply_text(tr(context, "exact_time"), reply_markup=exact_time_keyboard(context, interval))
        return CONTACT_HOUR
    context.user_data["contact_time"] = f"{text} ({interval})"
    return await finish_lead(update, context)

async def finish_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    user = update.effective_user
    t = T[lang(context)]
    sid = data.get("service")
    visible_service = service_name(context, sid) if sid in SERVICE_IDS else "—"
    price = money(data["estimate"], context) if data.get("estimate") is not None else "—"
    fields = [
        data.get("name", "—"), data.get("phone", "—"), visible_service,
        data.get("area", "—"), price, data.get("address", "—"),
        data.get("contact_time", "—"), str(user.id if user else "—")
    ]
    lead = t["admin_title"] + "\n\n" + "\n".join(f"{label}: {value}" for label, value in zip(T["hy"]["admin_fields"], fields))
    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=lead)
        except Exception:
            logger.exception("Could not send lead")
            await update.effective_message.reply_text(tr(context, "send_error"), reply_markup=main_keyboard(context))
            context.user_data.clear()
            return MENU
    else:
        logger.warning("OWNER_CHAT_ID is missing. Lead:\n%s", lead)
    await update.effective_message.reply_text(tr(context, "thanks"), reply_markup=main_keyboard(context))
    context.user_data.clear()
    return MENU

async def call_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(tr(context, "call_text"), reply_markup=main_keyboard(context))
    return MENU

async def unknown_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(tr(context, "unknown"), reply_markup=main_keyboard(context))
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text("Action cancelled / Գործողությունը չեղարկվեց / Действие отменено. Send /start.", reply_markup=language_keyboard())
    return LANG

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN was not found. Check your environment variables.")
    app = Application.builder().token(BOT_TOKEN).build()
    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            MENU: [
                MessageHandler(filters.Regex(r"^(🧹 Մեր ծառայությունները|🧹 Наши услуги|🧹 Our services)$"), show_services),
                MessageHandler(filters.Regex(r"^(💰 Մոտավոր հաշվարկել|💰 Рассчитать стоимость|💰 Estimate the price)$"), choose_estimate),
                MessageHandler(filters.Regex(r"^(📝 Ուղարկել հայտ|📝 Оставить заявку|📝 Submit a request)$"), start_request),
                MessageHandler(filters.Regex(r"^(📞 Զանգահարել մեզ|📞 Позвонить нам|📞 Call us)$"), call_us),
                MessageHandler(filters.Regex(r"^(🌐 Փոխել լեզուն|🌐 Сменить язык|🌐 Change language)$"), change_language),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_menu),
            ],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_service)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_area)],
            HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_hours)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            PHONE: [MessageHandler(filters.CONTACT, receive_contact), MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_address)],
            CONTACT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact_time)],
            CONTACT_HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact_hour)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conversation)
    logger.info("Your Clean Home multilingual Telegram bot is running.")
    app.run_polling()

if __name__ == "__main__":
    main()
