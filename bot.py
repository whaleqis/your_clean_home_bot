import os
import re
import logging

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID", "").strip()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MENU, SERVICE, AREA, HOURS, NAME, PHONE, ADDRESS, CONTACT_TIME, CONTACT_HOUR = range(9)

SERVICES = [
    "Ընթացիկ մաքրում",
    "Համալիր մաքրում",
    "Հետշինարարական մաքրում",
    "Գոլորշիով մաքրում",
    "Քիմմաքրում",
    "Արդուկում",
]

MAIN = "⬅️ Գլխավոր մենյու"
BACK = "⬅️ Նախորդ քայլ"
ESTIMATE = "💰 Մոտավոր հաշվարկել"
REQUEST = "📝 Ուղարկել հայտ"
SERVICES_BUTTON = "🧹 Մեր ծառայությունները"
CALL = "📞 Զանգահարել մեզ"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [SERVICES_BUTTON],
        [ESTIMATE],
        [REQUEST],
        [CALL],
    ],
    resize_keyboard=True,
)

SERVICE_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Ընթացիկ մաքրում", "Համալիր մաքրում"],
        ["Հետշինարարական մաքրում"],
        ["Գոլորշիով մաքրում", "Քիմմաքրում"],
        ["Արդուկում"],
        [MAIN],
    ],
    resize_keyboard=True,
)

def step_keyboard():
    return ReplyKeyboardMarkup([[BACK], [MAIN]], resize_keyboard=True)

PHONE_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📲 Ուղարկել հեռախոսահամարս", request_contact=True)],
        ["✍️ Մուտքագրել հեռախոսահամարը"],
        [BACK],
        [MAIN],
    ],
    resize_keyboard=True,
)

RESULT_KEYBOARD = ReplyKeyboardMarkup(
    [
        [REQUEST],
        [CALL],
        [ESTIMATE],
        [MAIN],
    ],
    resize_keyboard=True,
)


# Common area and ironing-hour choices reduce the amount of typing.
AREA_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["20 քմ", "30 քմ"],
        ["40 քմ", "50 քմ"],
        ["60 քմ", "70 քմ"],
        ["80 քմ", "100 քմ"],
        ["✍️ Այլ մակերես"],
        [BACK],
        [MAIN],
    ],
    resize_keyboard=True,
)

IRONING_HOURS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["1 ժամ", "2 ժամ"],
        ["3 ժամ", "4 ժամ"],
        ["✍️ Այլ քանակ"],
        [BACK],
        [MAIN],
    ],
    resize_keyboard=True,
)

TIME_INTERVALS = {
    "🌅 09:00–12:00": ["09:00", "10:00", "11:00"],
    "☀️ 12:00–15:00": ["12:00", "13:00", "14:00"],
    "🌤️ 15:00–18:00": ["15:00", "16:00", "17:00"],
    "🌙 18:00–21:00": ["18:00", "19:00", "20:00"],
}

CONTACT_TIME_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🌅 09:00–12:00", "☀️ 12:00–15:00"],
        ["🌤️ 15:00–18:00", "🌙 18:00–21:00"],
        ["🕒 Ցանկացած ժամ"],
        [BACK],
        [MAIN],
    ],
    resize_keyboard=True,
)

def exact_time_keyboard(interval):
    times = TIME_INTERVALS.get(interval, [])
    rows = [times[i:i + 2] for i in range(0, len(times), 2)]
    rows.extend([[BACK], [MAIN]])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def money(amount):
    return f"{amount:,.0f}".replace(",", " ") + " դրամ"


def calculate(service, area=None, hours=None):
    if service == "Ընթացիկ մաքրում":
        return max(14000, area * 350)
    if service == "Համալիր մաքրում":
        return max(26000, area * 650)
    if service == "Հետշինարարական մաքրում":
        return max(32000, area * 800)
    if service == "Գոլորշիով մաքրում":
        return 15000 if area < 10 else area * 1000
    if service == "Արդուկում":
        return hours * 4000
    return None


def extras(service):
    data = {
        "Ընթացիկ մաքրում": (
            "➕ Հավելյալ ծառայություններ\n\n"
            "• Լրացուցիչ սանհանգույց՝ 3 000 դրամ/հատ\n"
            "• Սառնարանի մաքրում՝ 3 000 դրամ\n"
            "• Պատշգամբի մաքրում՝ 2 000 դրամ\n"
            "• Արդուկում՝ 4 000 դրամ/ժամ\n"
            "• Կենդանիների առկայության դեպքում՝ 2 000 դրամ"
        ),
        "Համալիր մաքրում": (
            "➕ Հավելյալ ծառայություններ\n\n"
            "• Լրացուցիչ սանհանգույց՝ 5 000 դրամ\n"
            "• Սառնարանի մաքրում՝ 3 000 դրամ\n"
            "• Պատշգամբի մաքրում՝ 3 000 դրամ\n"
            "• Դարակների մաքրում՝ 10 000 դրամ\n"
            "• Գոլորշիով մաքրում՝ 5 000 դրամ\n"
            "• Վարագույրների լվացում՝ 2 000 դրամ/հատ\n"
            "• Արդուկում՝ 4 000 դրամ/ժամ\n"
            "• Կենդանիների առկայության դեպքում՝ 4 000 դրամ"
        ),
        "Հետշինարարական մաքրում": (
            "➕ Հավելյալ ծառայություններ\n\n"
            "• Դարակների մաքրում՝ 10 000 դրամ\n"
            "• Պատշգամբի մաքրում՝ 5 000 դրամ"
        ),
        "Գոլորշիով մաքրում": (
            "Գոլորշիով մաքրման վերջնական արժեքը կախված է մակերեսից "
            "և աշխատանքի ծավալից։"
        ),
        "Քիմմաքրում": (
            "🛋 Քիմմաքրման գներ\n\n"
            "• Բազկաթոռ՝ 2 500 դրամ\n"
            "• Երկտեղանի բազմոց՝ 8 000 դրամ\n"
            "• Եռատեղանի բազմոց՝ 10 000 դրամ\n"
            "• Երկտեղանի բազմոց + 2 բազկաթոռ՝ 10 000 դրամ\n"
            "• Եռատեղանի բազմոց + 2 բազկաթոռ՝ 12 000 դրամ\n"
            "• Անկյունային բազմոց՝ 15 000 դրամ\n"
            "• Փափուկ աթոռ՝ 2 000 դրամ\n"
            "• Փայտե աթոռ՝ 1 000 դրամ\n"
            "• Մեկտեղանի ներքնակ՝ 8 000 դրամ\n"
            "• Երկտեղանի ներքնակ՝ 12 000 դրամ\n"
            "• Մանկական ներքնակ՝ 6 000 դրամ"
        ),
        "Արդուկում": "Արդուկման արժեքը՝ 4 000 դրամ/ժամ։",
    }
    return data.get(service, "")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text(
        "Բարի գալուստ Your Clean Home 💚🧹\n\n"
        "Մենք կօգնենք Ձեր տունը դարձնել մաքուր, թարմ ու հարմարավետ։\n\n"
        "Ընտրեք ցանկալի տարբերակը ներքևի մենյուից։",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU


async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🧹 ՄԵՐ ԾԱՌԱՅՈՒԹՅՈՒՆՆԵՐԸ\n\n"
        "• Ընթացիկ մաքրում — տան կանոնավոր մաքրություն։\n\n"
        "• Համալիր մաքրում — տան մանրակրկիտ մաքրություն։\n\n"
        "• Հետշինարարական մաքրում — վերանորոգումից հետո մաքրություն։\n\n"
        "• Գոլորշիով մաքրում — համապատասխան մակերեսների մաքրում գոլորշու միջոցով։\n\n"
        "• Քիմմաքրում — փափուկ կահույքի և ներքնակների մաքրում։\n\n"
        "• Արդուկում — հագուստի արդուկման ծառայություն։\n\n"
        "Գինը կարող է փոխվել՝ կախված աշխատանքի ծավալից և հավելյալ ծառայություններից։",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU


async def choose_estimate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["flow"] = "estimate"
    await update.effective_message.reply_text(
        "Ընտրեք ծառայությունը՝ մոտավոր արժեքը հաշվարկելու համար։",
        reply_markup=SERVICE_KEYBOARD,
    )
    return SERVICE


async def start_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Preserve the service and estimate if the customer came from the calculator.
    if context.user_data.get("service") and context.user_data.get("estimate") is not None:
        context.user_data["flow"] = "request"
        await update.effective_message.reply_text(
            "Լրացնենք հայտը 💚\n\n"
            f"Ծառայություն՝ {context.user_data['service']}\n"
            f"Մոտավոր արժեք՝ {money(context.user_data['estimate'])}\n\n"
            "Ինչպե՞ս դիմենք Ձեզ։ Գրեք Ձեր անունը։",
            reply_markup=step_keyboard(),
        )
        return NAME

    context.user_data.clear()
    context.user_data["flow"] = "request"
    await update.effective_message.reply_text(
        "Լրացնենք հայտը 💚\n\nԸնտրեք Ձեզ հետաքրքրող ծառայությունը։",
        reply_markup=SERVICE_KEYBOARD,
    )
    return SERVICE


async def request_without_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["flow"] = "request"
    context.user_data["service"] = "Ծառայությունը կճշտվի զանգի ընթացքում"
    await update.effective_message.reply_text(
        "Իհարկե, կարող եք հայտ ուղարկել։ 💚\n\nԳրեք Ձեր անունը։",
        reply_markup=step_keyboard(),
    )
    return NAME


async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()

    if text == MAIN:
        return await start(update, context)

    if text not in SERVICES:
        await update.effective_message.reply_text(
            "Կներեք, չհասկացա ընտրությունը 😊\n"
            "Ընտրեք ծառայություններից մեկը կոճակներով։",
            reply_markup=SERVICE_KEYBOARD,
        )
        return SERVICE

    context.user_data["service"] = text

    if context.user_data.get("flow") == "request":
        await update.effective_message.reply_text(
            "Ինչպե՞ս դիմենք Ձեզ։ Գրեք Ձեր անունը։",
            reply_markup=step_keyboard(),
        )
        return NAME

    if text == "Քիմմաքրում":
        await update.effective_message.reply_text(
            extras(text) + "\n\n"
            "Մանրամասների համար զանգահարեք՝ 041 10 11 43, "
            "կամ սեղմեք «Ուղարկել հայտ», և մենք կզանգահարենք Ձեզ։",
            reply_markup=RESULT_KEYBOARD,
        )
        return MENU

    if text == "Արդուկում":
        await update.effective_message.reply_text(
            "Արդուկման արժեքը 4 000 դրամ է մեկ ժամի համար։\n"
            "Քանի՞ ժամ է Ձեզ անհրաժեշտ։ Օրինակ՝ 2։",
            reply_markup=step_keyboard(),
        )
        return HOURS

    await update.effective_message.reply_text(
        "Ընտրեք տարածքի մոտավոր մակերեսը կամ սեղմեք «✍️ Այլ մակերես»։",
        reply_markup=AREA_KEYBOARD,
    )
    return AREA


async def enter_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()

    if text == MAIN:
        return await start(update, context)
    if text == BACK:
        await update.effective_message.reply_text(
            "Ընտրեք ծառայությունը։",
            reply_markup=SERVICE_KEYBOARD,
        )
        return SERVICE

    if text == "✍️ Այլ մակերես":
        await update.effective_message.reply_text(
            "Գրեք տարածքի մակերեսը քառակուսի մետրերով։ Օրինակ՝ 65։",
            reply_markup=step_keyboard(),
        )
        return AREA

    match = re.search(r"\d+(?:[.,]\d+)?", text)
    if not match or float(match.group().replace(",", ".")) <= 0:
        await update.effective_message.reply_text(
            "Ընտրեք մակերեսը կոճակներից կամ սեղմեք «✍️ Այլ մակերես»։",
            reply_markup=AREA_KEYBOARD,
        )
        return AREA

    area = float(match.group().replace(",", "."))
    service = context.user_data["service"]
    price = calculate(service, area=area)

    context.user_data["area"] = f"{area:g} քմ"
    context.user_data["estimate"] = price

    await update.effective_message.reply_text(
        f"📐 Մակերես՝ {area:g} քմ\n"
        f"💰 Մոտավոր հիմնական արժեք՝ {money(price)}\n\n"
        "📌 Սա նախնական հաշվարկ է՝ առանց հավելյալ ծառայությունների։ "
        "Վերջնական արժեքը կարող է փոփոխվել՝ կախված տարածքի վիճակից և աշխատանքի ծավալից։\n\n"
        f"{extras(service)}\n\n"
        "Մանրամասների և վերջնական գինը ճշտելու համար զանգահարեք՝ 041 10 11 43, "
        "կամ սեղմեք «📝 Ուղարկել հայտ», և մենք կզանգահարենք Ձեզ։",
        reply_markup=RESULT_KEYBOARD,
    )
    return MENU


async def enter_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()

    if text == MAIN:
        return await start(update, context)
    if text == BACK:
        await update.effective_message.reply_text(
            "Ընտրեք ծառայությունը։",
            reply_markup=SERVICE_KEYBOARD,
        )
        return SERVICE

    if text == "✍️ Այլ քանակ":
        await update.effective_message.reply_text(
            "Մուտքագրեք արդուկման ժամերի քանակը։ Օրինակ՝ 5։",
            reply_markup=step_keyboard(),
        )
        return HOURS

    match = re.search(r"\d+(?:[.,]\d+)?", text)
    if not match or float(match.group().replace(",", ".")) <= 0:
        await update.effective_message.reply_text(
            "Ընտրեք ժամերի քանակը կոճակներից կամ սեղմեք «✍️ Այլ քանակ»։",
            reply_markup=IRONING_HOURS_KEYBOARD,
        )
        return HOURS

    hours = float(match.group().replace(",", "."))
    price = calculate("Արդուկում", hours=hours)
    context.user_data["area"] = f"{hours:g} ժամ"
    context.user_data["estimate"] = price

    await update.effective_message.reply_text(
        f"👔 Արդուկման մոտավոր արժեք՝ {money(price)}\n\n"
        "Վերջնական արժեքը կարող է կախված լինել աշխատանքի ծավալից։\n\n"
        "Մանրամասների համար զանգահարեք՝ 041 10 11 43 կամ սեղմեք "
        "«📝 Ուղարկել հայտ», և մենք կապ կհաստատենք Ձեզ հետ։",
        reply_markup=RESULT_KEYBOARD,
    )
    return MENU


async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()

    if text == MAIN:
        return await start(update, context)
    if text == BACK:
        await update.effective_message.reply_text(
            "Ընտրեք ծառայությունը։",
            reply_markup=SERVICE_KEYBOARD,
        )
        return SERVICE

    if len(text) < 2:
        await update.effective_message.reply_text(
            "Կներեք, չհասկացա անունը։ Խնդրում եմ գրեք Ձեր անունը։",
            reply_markup=step_keyboard(),
        )
        return NAME

    context.user_data["name"] = text
    await update.effective_message.reply_text(
        "Ուղարկեք Ձեր հեռախոսահամարը կամ ընտրեք ձեռքով մուտքագրելու տարբերակը։",
        reply_markup=PHONE_KEYBOARD,
    )
    return PHONE


async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()

    if text == MAIN:
        return await start(update, context)
    if text == BACK:
        await update.effective_message.reply_text(
            "Գրեք Ձեր անունը։",
            reply_markup=step_keyboard(),
        )
        return NAME

    if text == "✍️ Մուտքագրել հեռախոսահամարը":
        await update.effective_message.reply_text(
            "Մուտքագրեք հեռախոսահամարը, օրինակ՝ 091123456։",
            reply_markup=step_keyboard(),
        )
        return PHONE

    normalized = "".join(ch for ch in text if ch.isdigit() or ch == "+")
    digits = "".join(ch for ch in normalized if ch.isdigit())

    if len(digits) < 8:
        await update.effective_message.reply_text(
            "Հեռախոսահամարը կարծես ամբողջական չէ։ Փորձեք կրկին, օրինակ՝ 091123456։",
            reply_markup=PHONE_KEYBOARD,
        )
        return PHONE

    context.user_data["phone"] = normalized
    await update.effective_message.reply_text(
        "Նշեք հասցեն կամ թաղամասը։ Եթե դեռ չգիտեք, գրեք «Կճշտեմ»։",
        reply_markup=step_keyboard(),
    )
    return ADDRESS


async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.effective_message.contact

    if not contact or not contact.phone_number:
        await update.effective_message.reply_text(
            "Չհաջողվեց ստանալ հեռախոսահամարը։ Փորձեք կրկին։",
            reply_markup=PHONE_KEYBOARD,
        )
        return PHONE

    context.user_data["phone"] = contact.phone_number
    await update.effective_message.reply_text(
        "Նշեք հասցեն կամ թաղամասը։ Եթե դեռ չգիտեք, գրեք «Կճշտեմ»։",
        reply_markup=step_keyboard(),
    )
    return ADDRESS


async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()

    if text == MAIN:
        return await start(update, context)
    if text == BACK:
        await update.effective_message.reply_text(
            "Ուղարկեք կամ մուտքագրեք հեռախոսահամարը։",
            reply_markup=PHONE_KEYBOARD,
        )
        return PHONE

    if not text:
        await update.effective_message.reply_text(
            "Խնդրում եմ նշեք հասցեն կամ թաղամասը, կամ գրեք «Կճշտեմ»։",
            reply_markup=step_keyboard(),
        )
        return ADDRESS

    context.user_data["address"] = text
    await update.effective_message.reply_text(
        "📞 Ո՞ր ժամային միջակայքում է հարմար, որ կապ հաստատենք։",
        reply_markup=CONTACT_TIME_KEYBOARD,
    )
    return CONTACT_TIME


async def enter_contact_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()

    if text == MAIN:
        return await start(update, context)
    if text == BACK:
        await update.effective_message.reply_text(
            "Նշեք հասցեն կամ թաղամասը։",
            reply_markup=step_keyboard(),
        )
        return ADDRESS

    if text == "🕒 Ցանկացած ժամ":
        context.user_data["contact_time"] = "Ցանկացած ժամ"
        return await finish_lead(update, context)

    if text not in TIME_INTERVALS:
        await update.effective_message.reply_text(
            "Ընտրեք կապի հարմար ժամային միջակայքը կոճակներից։",
            reply_markup=CONTACT_TIME_KEYBOARD,
        )
        return CONTACT_TIME

    context.user_data["contact_interval"] = text
    await update.effective_message.reply_text(
        f"Ընտրել եք՝ {text}։ Ո՞ր ժամն է Ձեզ հարմար։",
        reply_markup=exact_time_keyboard(text),
    )
    return CONTACT_HOUR


async def enter_contact_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()

    if text == MAIN:
        return await start(update, context)
    if text == BACK:
        await update.effective_message.reply_text(
            "Ընտրեք կապի հարմար ժամային միջակայքը։",
            reply_markup=CONTACT_TIME_KEYBOARD,
        )
        return CONTACT_TIME

    interval = context.user_data.get("contact_interval")
    if interval not in TIME_INTERVALS or text not in TIME_INTERVALS[interval]:
        await update.effective_message.reply_text(
            "Ընտրեք կոնկրետ ժամը կոճակներից։",
            reply_markup=exact_time_keyboard(interval),
        )
        return CONTACT_HOUR

    context.user_data["contact_time"] = f"{text} ({interval})"
    return await finish_lead(update, context)


async def finish_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    user = update.effective_user

    lead = (
        "🆕 Your Clean Home — ՆՈՐ ՀԱՅՏ\n\n"
        f"👤 Անուն՝ {data.get('name', '—')}\n"
        f"📞 Հեռախոս՝ {data.get('phone', '—')}\n"
        f"🧹 Ծառայություն՝ {data.get('service', 'չի նշվել')}\n"
        f"📐 Մակերես / ժամեր՝ {data.get('area', 'չի նշվել')}\n"
        f"💰 Մոտավոր արժեք՝ "
        f"{money(data['estimate']) if data.get('estimate') is not None else 'չի հաշվարկվել'}\n"
        f"📍 Հասցե՝ {data.get('address', '—')}\n"
        f"🕒 Կապի հարմար ժամ՝ {data.get('contact_time', '—')}\n"
        f"🆔 Telegram ID՝ {user.id if user else '—'}"
    )

    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=lead)
        except Exception:
            logger.exception("Could not send lead")
            await update.effective_message.reply_text(
                "Հայտը ուղարկելիս խնդիր առաջացավ։ Խնդրում ենք զանգահարել՝ 041 10 11 43։",
                reply_markup=MAIN_KEYBOARD,
            )
            context.user_data.clear()
            return MENU
    else:
        logger.warning("OWNER_CHAT_ID is missing. Lead:\\n%s", lead)

    await update.effective_message.reply_text(
        "Շնորհակալություն, Ձեր հայտը ստացանք։ 💚\\n\\n"
        "Մեր թիմը կապ կհաստատի Ձեզ հետ՝ մանրամասները ճշտելու և վերջնական արժեքը ներկայացնելու համար։\\n\\n"
        "Կարող եք նաև զանգահարել՝ 041 10 11 43։",
        reply_markup=MAIN_KEYBOARD,
    )

    context.user_data.clear()
    return MENU


async def call_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📞 Զանգահարեք մեզ՝ 041 10 11 43։\n\nՍիրով կպատասխանենք Ձեր հարցերին։",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU


async def unknown_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Կներեք, չհասկացա Ձեր հաղորդագրությունը 😊\n\n"
        "Խնդրում եմ ընտրեք տարբերակներից մեկը ներքևի կոճակներով։",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU


async def unknown_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Կներեք, չհասկացա ընտրությունը 😊 Ընտրեք ծառայություններից մեկը կոճակներով։",
        reply_markup=SERVICE_KEYBOARD,
    )
    return SERVICE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text(
        "Գործողությունը չեղարկվեց։ Կարող եք սկսել նորից՝ /start հրամանով։",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN-ը չի գտնվել։ Ստուգեք .env ֆայլը։")

    app = Application.builder().token(BOT_TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r"^💰 Մոտավոր հաշվարկել$"), choose_estimate),
            MessageHandler(filters.Regex(r"^📝 Ուղարկել հայտ$"), start_request),
        ],
        states={
            MENU: [
                MessageHandler(filters.Regex(r"^🧹 Մեր ծառայությունները$"), show_services),
                MessageHandler(filters.Regex(r"^💰 Մոտավոր հաշվարկել$"), choose_estimate),
                MessageHandler(filters.Regex(r"^📝 Ուղարկել հայտ$"), start_request),
                MessageHandler(filters.Regex(r"^📞 Զանգահարել մեզ$"), call_us),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_menu),
            ],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_service)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_area)],
            HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_hours)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            PHONE: [
                MessageHandler(filters.CONTACT, receive_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone),
            ],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_address)],
            CONTACT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact_time)],
            CONTACT_HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact_hour)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conversation)
    logger.info("Your Clean Home bot is running.")
    app.run_polling()


if __name__ == "__main__":
    main()
