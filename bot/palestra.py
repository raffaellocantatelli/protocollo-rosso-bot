"""Calcolo onesto: Mifflin-St Jeor, BMI/Lorentz, tempi da letteratura.

Non è prescrizione medica. Peso ideale = fascia, non un numero magico.
"""

from __future__ import annotations

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import CONVERSATION_TIMEOUT
from bot.db import _now, connect

OBIETTIVO, SESSO, ETA, ALTEZZA, PESO, ATTIVITA = range(6)

FATTORI = {
    "sedentario": 1.2,
    "2-3": 1.375,
    "4-5": 1.55,
    "6+": 1.725,
}

SCHEDE = {
    "dimagrire": (
        "*Scheda forza + cammino* (3 giorni, full body)\n"
        "1. Squat o leg press — 3x8\n"
        "2. Panca o piegamenti — 3x8\n"
        "3. Rematore o trazioni — 3x8\n"
        "4. Hip hinge (stacco rumeno o hip thrust) — 3x8\n"
        "5. Cammino 7–9.000 passi il resto della settimana\n"
        "Il grasso scende col *deficit*. I pesi tengono il muscolo."
    ),
    "muscolo": (
        "*Scheda ipertrofia* (4 giorni)\n"
        "A. Squat 4x6–8 + affondi 3x10\n"
        "B. Panca 4x6–8 + military 3x8 + dip 3x8\n"
        "C. Stacco 3x5 + rematore 4x8 + trazioni 3x max\n"
        "D. Hip thrust 3x10 + curl/push 3x12 + core\n"
        "+1–2 kg sul bilanciere quando chiudi tutte le ripetizioni."
    ),
    "mantenere": (
        "*Mantenimento* (3 giorni)\n"
        "Squat, panca, rematore, hinge — 3x8 + cammino.\n"
        "Kcal di manutenzione. Non rincorrere la bilancia ogni giorno."
    ),
}


def _init() -> None:
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS corpo_profilo (
                telegram_id INTEGER PRIMARY KEY,
                sesso TEXT, eta INTEGER, altezza_cm REAL, peso_kg REAL,
                attivita TEXT, obiettivo TEXT,
                kcal INTEGER, proteine_g INTEGER, grassi_g INTEGER, carbo_g INTEGER,
                updated_at TEXT)"""
        )


def salva(tid: int, d: dict) -> None:
    _init()
    with connect() as conn:
        conn.execute(
            """INSERT INTO corpo_profilo
            (telegram_id,sesso,eta,altezza_cm,peso_kg,attivita,obiettivo,
             kcal,proteine_g,grassi_g,carbo_g,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET
             sesso=excluded.sesso, eta=excluded.eta, altezza_cm=excluded.altezza_cm,
             peso_kg=excluded.peso_kg, attivita=excluded.attivita,
             obiettivo=excluded.obiettivo, kcal=excluded.kcal,
             proteine_g=excluded.proteine_g, grassi_g=excluded.grassi_g,
             carbo_g=excluded.carbo_g, updated_at=excluded.updated_at""",
            (
                tid, d["sesso"], d["eta"], d["altezza_cm"], d["peso_kg"],
                d["attivita"], d["obiettivo"], d["kcal"], d["proteine_g"],
                d["grassi_g"], d["carbo_g"], _now(),
            ),
        )


def carica(tid: int) -> dict | None:
    _init()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM corpo_profilo WHERE telegram_id=?", (tid,)
        ).fetchone()
    return dict(row) if row else None


def _num(s: str) -> float | None:
    s = (s or "").strip().replace(",", ".").replace("cm", "").replace("kg", "")
    try:
        return float(s)
    except ValueError:
        return None


def piano_peso(sesso: str, h: float, w: float, ob: str) -> dict:
    hm = h / 100.0
    bmi = w / (hm * hm)
    fascia_min = 20.0 * hm * hm
    fascia_max = 24.9 * hm * hm
    centro = 22.0 * hm * hm
    if sesso == "m":
        lorentz = h - 100 - (h - 150) / 4.0
    else:
        lorentz = h - 100 - (h - 150) / 2.5
    if ob == "dimagrire":
        target = min(w - 0.5, max(fascia_min, min(centro, fascia_max)))
        if w <= fascia_max:
            target = min(w, centro)
        ritmo = 0.6
        ritmo_lento, ritmo_veloce = 0.4, 0.8
    elif ob == "muscolo":
        target = max(w + 0.5, min(fascia_max, max(centro, w + 2.0)))
        if w >= fascia_min:
            target = min(fascia_max, w + 3.0)
        ritmo = 0.25
        ritmo_lento, ritmo_veloce = 0.15, 0.4
    else:
        target = w
        ritmo = ritmo_lento = ritmo_veloce = 0.0
    delta = target - w
    if abs(delta) < 0.8:
        sett = sett_min = sett_max = 0
    else:
        kg = abs(delta)
        sett = max(4, round(kg / ritmo))
        sett_min = max(3, round(kg / max(ritmo_veloce, 0.1)))
        sett_max = max(sett_min + 2, round(kg / max(ritmo_lento, 0.1)))
    return {
        "bmi": round(bmi, 1),
        "fascia_min": round(fascia_min, 1),
        "fascia_max": round(fascia_max, 1),
        "centro": round(centro, 1),
        "lorentz": round(lorentz, 1),
        "target": round(target, 1),
        "delta": round(delta, 1),
        "ritmo": ritmo,
        "settimane": sett,
        "settimane_min": sett_min,
        "settimane_max": sett_max,
    }


def calcola(sesso: str, eta: int, h: float, w: float, att: str, ob: str) -> dict:
    bmr = 10 * w + 6.25 * h - 5 * eta + (5 if sesso == "m" else -161)
    tdee = bmr * FATTORI[att]
    if ob == "dimagrire":
        kcal = max(1200, tdee - 500)
        prot_kg = 1.8
    elif ob == "muscolo":
        kcal = tdee + 250
        prot_kg = 2.0
    else:
        kcal = tdee
        prot_kg = 1.6
    prot = round(prot_kg * w)
    fat = round(max(0.8 * w, 0.25 * kcal / 9))
    carb = max(0, round((kcal - prot * 4 - fat * 9) / 4))
    out = {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "kcal": round(kcal),
        "proteine_g": prot,
        "grassi_g": fat,
        "carbo_g": carb,
    }
    out.update(piano_peso(sesso, h, w, ob))
    return out


def _blocco_tempo(d: dict) -> str:
    ob = d["obiettivo"]
    if ob == "mantenere" or d.get("settimane", 0) == 0:
        return (
            f"BMI `{d.get('bmi', '?')}` \u00b7 fascia sana ~ "
            f"`{d.get('fascia_min')}`–`{d.get('fascia_max')}` kg "
            f"(BMI 20–24.9). Centro `{d.get('centro')}` kg.\n"
            f"Lorentz (altra stima) `{d.get('lorentz')}` kg.\n"
            "Sei già vicino: tieni le kcal di manutenzione e la scheda."
        )
    verso = "perdere" if d["delta"] < 0 else "mettere"
    return (
        f"BMI oggi `{d.get('bmi')}`\n"
        f"Fascia di peso (BMI 20–24.9): `{d.get('fascia_min')}`–`{d.get('fascia_max')}` kg\n"
        f"Punto medio (BMI 22): `{d.get('centro')}` kg\n"
        f"Lorentz: `{d.get('lorentz')}` kg\n"
        f"*Bersaglio di questo ciclo:* `{d.get('target')}` kg "
        f"({verso} `{abs(d['delta'])}` kg)\n"
        f"Ritmo onesto: ~`{d.get('ritmo')}` kg/settimana\n"
        f"*Tempo stimato:* `{d.get('settimane_min')}`–`{d.get('settimane_max')}` settimane "
        f"(centro ~`{d.get('settimane')}`).\n"
        "Le prime 1–2 settimane la bilancia muove anche acqua. "
        "Conta la media di 7 giorni, non un lunedì."
    )


def _scheda_testo(d: dict) -> str:
    ob = d["obiettivo"]
    return (
        f"*Profilo* — stima, non prescrizione\n\n"
        f"{d['sesso'].upper()}, {d['eta']} anni, {d['altezza_cm']:.0f} cm, {d['peso_kg']:.1f} kg\n"
        f"Obiettivo: *{ob}* \u00b7 attività: {d['attivita']}\n\n"
        f"{_blocco_tempo(d)}\n\n"
        f"BMR ~ `{d.get('bmr', '?')}` \u00b7 manutenzione `{d.get('tdee', d['kcal'])}` kcal\n"
        f"*Target oggi:* `{d['kcal']}` kcal\n"
        f"Proteine `{d['proteine_g']}` g \u00b7 grassi `{d['grassi_g']}` g \u00b7 carbo `{d['carbo_g']}` g\n"
        f"Grassi: EVO, uova, pesce, frutta secca.\n\n"
        f"{SCHEDE[ob]}\n\n"
        f"P6: a metà del tempo stimato, se il peso non ha fatto metà strada, "
        f"ricalcola con /palestra. Cade se copi le kcal e salti i pesi.\n"
        f"Fonti: Mifflin 1990; BMI OMS; Lorentz; ISSN 1.6–2.2 g/kg; "
        f"calo ~0.5–0.8 kg/sett; massa ~0.15–0.4 kg/sett."
    )


async def cmd_palestra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["corpo"] = {}
    await update.message.reply_text(
        "Obiettivo? Ti do fascia di peso, bersaglio e settimane stimate.",
        reply_markup=ReplyKeyboardMarkup(
            [["dimagrire", "muscolo"], ["mantenere", "/annulla"]],
            resize_keyboard=True,
        ),
    )
    return OBIETTIVO


async def cmd_scheda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    row = carica(update.effective_user.id)
    if not row:
        await update.message.reply_text("Nessun profilo. /palestra per crearne uno.")
        return
    extra = calcola(
        row["sesso"], row["eta"], row["altezza_cm"], row["peso_kg"],
        row["attivita"], row["obiettivo"],
    )
    row.update(extra)
    await update.message.reply_text(_scheda_testo(row), parse_mode=ParseMode.MARKDOWN)


async def set_obiettivo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = (update.message.text or "").strip().lower()
    if t not in ("dimagrire", "muscolo", "mantenere"):
        await update.message.reply_text("Scrivi: dimagrire, muscolo o mantenere.")
        return OBIETTIVO
    context.user_data.setdefault("corpo", {})["obiettivo"] = t
    await update.message.reply_text(
        "Sesso biologico per la formula BMR:",
        reply_markup=ReplyKeyboardMarkup([["m", "f"], ["/annulla"]], resize_keyboard=True),
    )
    return SESSO


async def set_sesso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = (update.message.text or "").strip().lower()
    if t not in ("m", "f"):
        await update.message.reply_text("m oppure f.")
        return SESSO
    context.user_data["corpo"]["sesso"] = t
    await update.message.reply_text("Età (anni):", reply_markup=ReplyKeyboardRemove())
    return ETA


async def set_eta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    n = _num(update.message.text or "")
    if n is None or n < 14 or n > 90:
        await update.message.reply_text("Età tra 14 e 90.")
        return ETA
    context.user_data["corpo"]["eta"] = int(n)
    await update.message.reply_text("Altezza in cm (es. 178):")
    return ALTEZZA


async def set_altezza(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    n = _num(update.message.text or "")
    if n and n < 3:
        n *= 100
    if n is None or n < 140 or n > 220:
        await update.message.reply_text("Altezza in cm, tipo 178.")
        return ALTEZZA
    context.user_data["corpo"]["altezza_cm"] = n
    await update.message.reply_text("Peso in kg (es. 78.5):")
    return PESO


async def set_peso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    n = _num(update.message.text or "")
    if n is None or n < 40 or n > 220:
        await update.message.reply_text("Peso in kg, tipo 78.")
        return PESO
    context.user_data["corpo"]["peso_kg"] = n
    await update.message.reply_text(
        "Quante volte ti muovi / palestra a settimana?",
        reply_markup=ReplyKeyboardMarkup(
            [["sedentario", "2-3"], ["4-5", "6+"]], resize_keyboard=True
        ),
    )
    return ATTIVITA


async def set_attivita(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    t = (update.message.text or "").strip().lower()
    if t not in FATTORI:
        await update.message.reply_text("sedentario, 2-3, 4-5 oppure 6+.")
        return ATTIVITA
    d = context.user_data["corpo"]
    d["attivita"] = t
    calc = calcola(d["sesso"], d["eta"], d["altezza_cm"], d["peso_kg"], t, d["obiettivo"])
    d.update(calc)
    salva(update.effective_user.id, d)
    await update.message.reply_text(
        _scheda_testo(d),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Calcolo interrotto.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def build_palestra_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("palestra", cmd_palestra),
            CommandHandler("fisico", cmd_palestra),
        ],
        states={
            OBIETTIVO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_obiettivo)],
            SESSO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_sesso)],
            ETA: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_eta)],
            ALTEZZA: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_altezza)],
            PESO: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_peso)],
            ATTIVITA: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_attivita)],
        },
        fallbacks=[CommandHandler("annulla", cancel)],
        name="palestra",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
        allow_reentry=True,
    )
