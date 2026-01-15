from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# التوكن تبع البوت
TOKEN = "8513164221:AAHdqyseYrSJmbJXRBCwtj4Nj8gIUbQX29c"

# رقم تيليجرام تبعك للأدمن
ADMIN_ID = 123456789  # غيّر هذا برقمك

# طرق الدفع المتاحة
PAYMENT_METHODS = ["💵 كاش", "🏦 شام كاش", "💳 هرم"]

# الحد الأدنى للشحن
MIN_SHIP_AMOUNT = 5000

# بيانات الزبون (رصيد داخلي)
user_balances = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📲 تعبئة رصيد", "💰 رصيدي / سحب"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "أهلاً! 👋\nاختر الخدمة:", reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    user_id = user.id

    if user_id not in user_balances:
        user_balances[user_id] = 0

    state = context.user_data.get("state")

    if text == "📲 تعبئة رصيد":
        context.user_data["state"] = "awaiting_amount"
        await update.message.reply_text(f"أدخل المبلغ (≥ {MIN_SHIP_AMOUNT} ليرة):")
        return

    if text == "💰 رصيدي / سحب":
        balance = user_balances[user_id]
        if balance == 0:
            await update.message.reply_text("رصيدك الحالي: 0 ليرة\nلا يوجد رصيد للسحب.")
            return
        context.user_data["state"] = "awaiting_withdraw_amount"
        await update.message.reply_text(f"رصيدك الحالي: {balance} ليرة\nأدخل المبلغ الذي تريد سحبه:")
        return

    if state == "awaiting_amount":
        try:
            amount = int(text)
            if amount < MIN_SHIP_AMOUNT:
                await update.message.reply_text(f"المبلغ أقل من الحد الأدنى ({MIN_SHIP_AMOUNT} ليرة).")
                return
            context.user_data["amount"] = amount
            context.user_data["state"] = "awaiting_id"
            await update.message.reply_text("أدخل ID الخاص بك:")
        except ValueError:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return

    if state == "awaiting_id":
        context.user_data["id"] = text
        context.user_data["state"] = "awaiting_payment"
        keyboard = [[method] for method in PAYMENT_METHODS]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("اختر طريقة الدفع:", reply_markup=reply_markup)
        return

    if state == "awaiting_payment":
        if text not in PAYMENT_METHODS:
            await update.message.reply_text("اختر طريقة دفع من القائمة.")
            return
        context.user_data["payment"] = text

        # إشعار للزبون
        await update.message.reply_text(
            f"📩 تم إرسال طلبك بنجاح!\n"
            f"💰 المبلغ: {context.user_data['amount']} ليرة\n"
            f"🆔 ID: {context.user_data['id']}\n"
            f"💳 الدفع: {context.user_data['payment']}\n"
            f"✅ سيتم تعبئته يدوياً بعد الدفع."
        )

        # إشعار للأدمن
        admin_msg = (
            f"📩 طلب تعبئة جديد:\n\n"
            f"👤 الاسم: {user.full_name}\n"
            f"🆔 ID: {context.user_data['id']}\n"
            f"💰 المبلغ: {context.user_data['amount']} ليرة\n"
            f"💳 الدفع: {context.user_data['payment']}\n"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)

        # تحديث الرصيد الداخلي بعد الدفع
        user_balances[user_id] += context.user_data['amount']

        context.user_data.clear()
        return

    if state == "awaiting_withdraw_amount":
        try:
            withdraw_amount = int(text)
            balance = user_balances[user_id]
            if withdraw_amount > balance:
                await update.message.reply_text(f"رصيدك لا يكفي للسحب ({balance} ليرة).")
                return
            context.user_data["withdraw_amount"] = withdraw_amount
            context.user_data["state"] = "awaiting_withdraw_payment"

            keyboard = [[method] for method in PAYMENT_METHODS]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("اختر طريقة الدفع للسحب:", reply_markup=reply_markup)
        except ValueError:
            await update.message.reply_text("الرجاء إدخال رقم صالح.")
        return

    if state == "awaiting_withdraw_payment":
        if text not in PAYMENT_METHODS:
            await update.message.reply_text("اختر طريقة دفع من القائمة.")
            return
        withdraw_amount = context.user_data["withdraw_amount"]
        user_balances[user_id] -= withdraw_amount

        # إشعار للزبون
        await update.message.reply_text(
            f"📩 تم إرسال طلب السحب بنجاح!\n"
            f"💰 المبلغ: {withdraw_amount} ليرة\n"
            f"💳 الدفع: {text}\n"
            f"✅ سيتم تنفيذه يدوياً."
        )

        # إشعار للأدمن
        admin_msg = (
            f"📩 طلب سحب جديد:\n\n"
            f"👤 الاسم: {user.full_name}\n"
            f"💰 المبلغ: {withdraw_amount} ليرة\n"
            f"💳 الدفع: {text}\n"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)

        context.user_data.clear()
        return

    await update.message.reply_text("الرجاء اختيار خيار من القائمة 👆")

# إعداد التطبيق وتشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
