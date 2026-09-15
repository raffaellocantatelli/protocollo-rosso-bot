"""/rrr — sottomenu. Protocollo prima, extra dopo."""

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

CHIUDI = "Chiudi menu"

RIGHE = [
    ["/tesi", "/strati", "/p5p6"],
    ["/santuario", "/tieni_aperto", "/lista"],
    ["/azione", "/veli", "/etichetta"],
    ["/testimone", "/fuori", "/libro"],
    ["/palestra", "/corpo", "/metodo"],
    ["/registro", "/ping", CHIUDI],
]

TASTIERA = ReplyKeyboardMarkup(RIGHE, resize_keyboard=True, is_persistent=False)


async def cmd_rrr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Protocollo in alto. Extra sotto. Tocca un comando.",
        reply_markup=TASTIERA,
    )


async def cmd_chiudi_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Menu chiuso. /rrr per riaprirlo.",
        reply_markup=ReplyKeyboardRemove(),
    )
