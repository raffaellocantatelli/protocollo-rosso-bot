"""
Handler — Protocollo Rosso Bot.
Ogni risposta rispetta gli strati e le leggi P5/P6.
Non chiude una possibilità aperta. Non spaccia il bot per una coscienza.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

from bot.config import CONVERSATION_TIMEOUT

from . import db
from . import epistemic
from . import texts
from .states import ActionState, EtichettaState, PossibilityState, SanctuaryState, VeloState

RIAPERTURE_QUANTICHE = [
    "Una chiusura non è ancora una prova.\n\nTieni aperta questa possibilità come `IPOTESI` — senza trasformarla in certezza, e senza chiuderla prima che sia il momento.",
    "La chiusura che senti è reale — ma non è definitiva. È uno strato, non la realtà intera. Usa /tieni\\_aperto se vuoi depositare questa tensione senza risolverla.",
    "Ogni «non posso» è un invito a verificare: *non posso perché è impossibile, o non posso perché non ho ancora trovato il modo?* Sono due cose diverse nello strato tecnico.",
    "Il dubbio non è il nemico della possibilità. È la sua forma più onesta.\n\nCiò che chiude non è il dubbio — è la certezza prematura che il dubbio sia definitivo. Scrivi quello che senti con /etichetta.",
    "Quello che descrivi come impossibile potrebbe essere `IPOTESI`.\n\nAnche l'impossibilità ha bisogno di P6: *come mostrerebbe di essere falsa?* Se non lo sai, allora nemmeno l'impossibilità è certa.",
]

_RIAPERTURA_IDX: dict[int, int] = {}


def _prossima_riapertura(user_id: int) -> str:
    idx = _RIAPERTURA_IDX.get(user_id, 0)
    risposta = RIAPERTURE_QUANTICHE[idx % len(RIAPERTURE_QUANTICHE)]
    _RIAPERTURA_IDX[user_id] = idx + 1
    return risposta


async def _ensure(update: Update) -> None:
    user = update.effective_user
    fn = getattr(db, "ensure_user", None) or getattr(db, "upsert_user")
    result = fn(user.id, user.username, user.first_name)
    if hasattr(result, "__await__"):
        await result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure(update)
    await update.message.reply_text(
        texts.WELCOME,
        parse_mode=ParseMode.MARKDOWN,
    )


async def tesi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        texts.TESI_GRANDE,
        parse_mode=ParseMode.MARKDOWN,
    )


async def strati(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        texts.STRATI,
        parse_mode=ParseMode.MARKDOWN,
    )


async def p5p6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        texts.P5_P6,
        parse_mode=ParseMode.MARKDOWN,
    )


async def aiuto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        texts.HELP,
        parse_mode=ParseMode.MARKDOWN,
    )


async def stato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure(update)
    try:
        counts = db.user_counts(update.effective_user.id)
        possibilita = counts.get("possibilities", 0)
        azioni = counts.get("actions", 0)
        santuari = counts.get("sanctuary_completed", 0)
    except Exception:
        possibilita = azioni = santuari = 0
    await update.message.reply_text(
        f"*Diario tecnico*\n\nPossibilità aperte: `{possibilita}`\nAzioni registrate: `{azioni}`\nSantuari completati: `{santuari}`\n\n_Ogni dato è nello strato tecnico. Nessuna di queste cifre conferma la tesi._",
        parse_mode=ParseMode.MARKDOWN,
    )


async def santuario_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _ensure(update)
    await update.message.reply_text(
        texts.SANTUARIO_INTRO,
        parse_mode=ParseMode.MARKDOWN,
    )
    return SanctuaryState.WAITING_ENTER


async def santuario_enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nxt, ok = epistemic.sanctuary_advance(
        SanctuaryState.WAITING_ENTER, update.message.text or ""
    )
    if ok:
        visit = db.log_sanctuary_visit if hasattr(db, "log_sanctuary_visit") else None
        if visit:
            result = visit(update.effective_user.id, completed=False)
            if hasattr(result, "__await__"):
                await result
        elif hasattr(db, "start_sanctuary"):
            context.user_data["sanctuary_visit_id"] = db.start_sanctuary(update.effective_user.id)
        await update.message.reply_text(
            texts.SANTUARIO_SILENCE,
            parse_mode=ParseMode.MARKDOWN,
        )
        return nxt
    await update.message.reply_text(
        "Scrivi *entro* o premi /entra per varcare la soglia.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return SanctuaryState.WAITING_ENTER


async def santuario_silence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nxt, ok = epistemic.sanctuary_advance(
        SanctuaryState.SILENCE, update.message.text or ""
    )
    if ok:
        await update.message.reply_text(
            texts.SANTUARIO_LIGHT,
            parse_mode=ParseMode.MARKDOWN,
        )
        return nxt
    await update.message.reply_text(
        "Quando sei pronto, scrivi *luce*.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return SanctuaryState.SILENCE


async def santuario_light(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nxt, ok = epistemic.sanctuary_advance(
        SanctuaryState.LIGHT, update.message.text or ""
    )
    if ok:
        await update.message.reply_text(
            texts.SANTUARIO_ALTAR,
            parse_mode=ParseMode.MARKDOWN,
        )
        return nxt
    await update.message.reply_text(
        "Quando sei pronto, scrivi *altare*.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return SanctuaryState.LIGHT


async def santuario_altar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nxt, ok = epistemic.sanctuary_advance(
        SanctuaryState.ALTAR, update.message.text or ""
    )
    if ok:
        await update.message.reply_text(
            texts.SANTUARIO_CANDLE,
            parse_mode=ParseMode.MARKDOWN,
        )
        return nxt
    await update.message.reply_text(
        "Scrivi *accendo* quando vuoi compiere il gesto.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return SanctuaryState.ALTAR


async def santuario_candle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nxt, ok = epistemic.sanctuary_advance(
        SanctuaryState.CANDLE, update.message.text or ""
    )
    if ok:
        if hasattr(db, "log_sanctuary_visit"):
            result = db.log_sanctuary_visit(update.effective_user.id, completed=True)
            if hasattr(result, "__await__"):
                await result
        elif hasattr(db, "complete_sanctuary"):
            vid = context.user_data.get("sanctuary_visit_id")
            if vid:
                db.complete_sanctuary(vid)
        if hasattr(db, "add_epistemic"):
            db.add_epistemic(
                update.effective_user.id,
                "TECNICO",
                "visita al Santuario completata",
                source="santuario",
                how_falls="cade se completed_at è vuoto",
            )
        await update.message.reply_text(
            texts.SANTUARIO_EXIT,
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "Scrivi *esco* o /esci quando vuoi uscire.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return SanctuaryState.CANDLE


async def santuario_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("possibility", None)
    context.user_data.pop("action_text", None)
    await update.message.reply_text(
        "Percorso interrotto. Nessun gesto è stato forzato. Nessuna possibilità è stata chiusa."
    )
    return ConversationHandler.END


async def tieni_aperto_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        texts.TIENI_APERTO_HELP,
        parse_mode=ParseMode.MARKDOWN,
    )
    return PossibilityState.WAITING_TEXT


async def tieni_aperto_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text or text.startswith("/"):
        await update.message.reply_text(
            "Scrivi la possibilità che vuoi tenere aperta (senza /)."
        )
        return PossibilityState.WAITING_TEXT
    context.user_data["possibility"] = text
    await update.message.reply_text(
        texts.P6_PROMPT,
        parse_mode=ParseMode.MARKDOWN,
    )
    return PossibilityState.WAITING_P6


async def tieni_aperto_p6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = (update.message.text or "").strip()
    text = (context.user_data.get("possibility") or "").strip()
    if not text:
        await update.message.reply_text(
            "Non ho più il testo. Riscrivi la possibilità."
        )
        return PossibilityState.WAITING_TEXT

    skipped = raw.lower() in {"/salta", "salta", "non so", "non lo so", "unknown"}
    how_falls = epistemic.P6_UNKNOWN if skipped or not raw or raw.startswith("/") else raw

    pid = db.add_possibility(update.effective_user.id, text, how_falls=how_falls)
    if hasattr(db, "add_epistemic"):
        db.add_epistemic(
            update.effective_user.id,
            "IPOTESI",
            text,
            source="tieni_aperto",
            how_falls=how_falls,
        )
    context.user_data.pop("possibility", None)
    await update.message.reply_text(
        f"Possibilità custodita come `IPOTESI` (id {pid}).\n\n"
        f"P6: _{how_falls}_\n\n"
        "Non verrà mai trasformata in certezza da questo bot.\nUsa /lista per rivederle.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ConversationHandler.END


async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.list_possibilities(update.effective_user.id)
    if not rows:
        await update.message.reply_text(
            "Nessuna possibilità aperta ancora.\nUsa /tieni\\_aperto per depositarne una.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    lines = ["*Le tue possibilità aperte* (tutte etichettate `IPOTESI`):\n"]
    for row in rows:
        if isinstance(row, dict):
            text = row.get("text") or ""
            rid = row.get("id")
            p6 = row.get("how_falls") or epistemic.P6_UNKNOWN
        else:
            text = row[1]
            rid = row[0]
            p6 = epistemic.P6_UNKNOWN
        short = text if len(text) < 80 else text[:77] + "…"
        lines.append(f"• `{rid}` — {short}\n  P6: _{p6}_")

    await update.message.reply_text("\n".join(lines)[:3900], parse_mode=ParseMode.MARKDOWN)


async def azione_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        texts.AZIONE_PROMPT,
        parse_mode=ParseMode.MARKDOWN,
    )
    return ActionState.WAITING_DESCRIPTION


async def azione_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text or text.startswith("/"):
        await update.message.reply_text("Descrivi l'azione concreta e verificabile.")
        return ActionState.WAITING_DESCRIPTION
    context.user_data["action_text"] = text
    await update.message.reply_text(
        texts.AZIONE_VERIFY_PROMPT,
        parse_mode=ParseMode.MARKDOWN,
    )
    return ActionState.WAITING_VERIFY


async def azione_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = (update.message.text or "").strip()
    text = (context.user_data.get("action_text") or "").strip()
    if not text:
        await update.message.reply_text("Non ho più l'azione. Riscrivila.")
        return ActionState.WAITING_DESCRIPTION

    skipped = raw.lower() in {"/salta", "salta", "nessuno", "non so"}
    if skipped or not raw or raw.startswith("/"):
        how = "dichiarato dall'utente; verifica esterna non specificata"
    else:
        how = raw

    aid = db.add_action(update.effective_user.id, text, how_verifiable=how)
    if hasattr(db, "add_epistemic"):
        db.add_epistemic(
            update.effective_user.id,
            "TECNICO",
            text,
            source="azione",
            how_falls="cade se un terzo non può controllare che sia accaduta",
        )
    context.user_data.pop("action_text", None)
    await update.message.reply_text(
        f"Azione registrata nello *strato tecnico* (id {aid}).\n\n"
        f"Chi può verificarla: _{how}_\n\n"
        "È un dato. Non è una dichiarazione di fede.\nGrazie per non aver finto.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ConversationHandler.END


async def veli_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        texts.VELI,
        parse_mode=ParseMode.MARKDOWN,
    )
    return VeloState.WAITING_CHOICE


async def veli_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    mapping = {
        "1": texts.VELO_1,
        "2": texts.VELO_2,
        "3": texts.VELO_3,
    }
    if text not in mapping:
        await update.message.reply_text("Scrivi 1, 2 o 3.")
        return VeloState.WAITING_CHOICE

    await update.message.reply_text(mapping[text], parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


async def etichetta_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Incolla o scrivi l'affermazione che vuoi etichettare.\nTi aiuterò a collocarla nello strato corretto — senza mai chiudere ciò che è aperto."
    )
    return EtichettaState.WAITING_TEXT


async def etichetta_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Scrivi un testo da etichettare.")
        return EtichettaState.WAITING_TEXT

    judged = epistemic.classify(text)
    if hasattr(db, "add_labeled"):
        db.add_labeled(update.effective_user.id, text, judged.layer)
    if hasattr(db, "add_epistemic"):
        db.add_epistemic(
            update.effective_user.id,
            judged.layer,
            text,
            source="etichetta",
            how_falls=judged.how_falls,
        )
    p6 = f"\nP6: {judged.how_falls}" if judged.how_falls else ""
    await update.message.reply_text(
        f"*Testo ricevuto*\n\n_{text[:500]}_\n\n*Etichetta proposta:* `{judged.layer}`\n\n{judged.note}{p6}\n\nRicorda P5: se sei tu l'unico a confermarla, non è una conferma.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ConversationHandler.END


async def messaggio_libero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return

    if epistemic.is_closure(text):
        risposta = _prossima_riapertura(update.effective_user.id)
        await update.message.reply_text(risposta, parse_mode=ParseMode.MARKDOWN)
        return

    label = epistemic.classify(text)
    if label.layer == "RISONANZA":
        await update.message.reply_text(
            "_Apertura rilevata._\n\nQuesto non dimostra la tesi. Porta la stessa qualità in un'azione reale — usa /azione per registrarla.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await update.message.reply_text(
        "Usa /aiuto per i comandi. Niente è stato chiuso.",
    )


def build_conversation_handlers():
    sanctuary = ConversationHandler(
        entry_points=[CommandHandler("santuario", santuario_entry)],
        states={
            SanctuaryState.WAITING_ENTER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, santuario_enter),
                CommandHandler("entra", santuario_enter),
            ],
            SanctuaryState.SILENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, santuario_silence),
            ],
            SanctuaryState.LIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, santuario_light),
            ],
            SanctuaryState.ALTAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, santuario_altar),
            ],
            SanctuaryState.CANDLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, santuario_candle),
                CommandHandler("esci", santuario_candle),
            ],
        },
        fallbacks=[CommandHandler("annulla", santuario_cancel), CommandHandler("cancel", santuario_cancel)],
        allow_reentry=True,
        name="santuario",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )

    possibility = ConversationHandler(
        entry_points=[CommandHandler("tieni_aperto", tieni_aperto_entry)],
        states={
            PossibilityState.WAITING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tieni_aperto_text),
            ],
            PossibilityState.WAITING_P6: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tieni_aperto_p6),
                CommandHandler("salta", tieni_aperto_p6),
            ],
        },
        fallbacks=[CommandHandler("annulla", santuario_cancel)],
        name="tieni_aperto",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )

    action = ConversationHandler(
        entry_points=[CommandHandler("azione", azione_entry)],
        states={
            ActionState.WAITING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, azione_description),
            ],
            ActionState.WAITING_VERIFY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, azione_verify),
                CommandHandler("salta", azione_verify),
            ],
        },
        fallbacks=[CommandHandler("annulla", santuario_cancel)],
        name="azione",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )

    velo = ConversationHandler(
        entry_points=[CommandHandler("veli", veli_entry)],
        states={
            VeloState.WAITING_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, veli_choice),
            ],
        },
        fallbacks=[CommandHandler("annulla", santuario_cancel)],
        name="veli",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )

    etichetta = ConversationHandler(
        entry_points=[CommandHandler("etichetta", etichetta_entry)],
        states={
            EtichettaState.WAITING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, etichetta_process),
            ],
        },
        fallbacks=[CommandHandler("annulla", santuario_cancel)],
        name="etichetta",
        persistent=True,
        conversation_timeout=CONVERSATION_TIMEOUT,
    )

    return [sanctuary, possibility, action, velo, etichetta]


async def registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not hasattr(db, "list_epistemic"):
        await update.message.reply_text("Registro non disponibile in questa build.")
        return
    rows = db.list_epistemic(update.effective_user.id)
    if not rows:
        await update.message.reply_text(
            "Registro epistemico vuoto.\nSi riempie con /tieni\\_aperto, /azione, /etichetta, /santuario.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    lines = ["*Registro epistemico* (non è una prova del «già»):\n"]
    for row in rows:
        snippet = row["text"]
        if len(snippet) > 70:
            snippet = snippet[:67] + "…"
        p6 = row["how_falls"] or "—"
        lines.append(f"• `{row['layer']}` _{row['source']}_\n  {snippet}\n  P6: {p6}")
    await update.message.reply_text("\n".join(lines)[:3900], parse_mode=ParseMode.MARKDOWN)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Qui. Strato tecnico: vivo. Nessuna tesi confermata.",
    )


async def cmd_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comando non riconosciuto. /aiuto per l'elenco. Niente è stato chiuso."
    )


async def cmd_annulla_idle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nessun percorso aperto da chiudere.")


def build_command_handlers():
    return [
        CommandHandler("start", start),
        CommandHandler("tesi", tesi),
        CommandHandler("strati", strati),
        CommandHandler("p5p6", p5p6),
        CommandHandler("lista", lista),
        CommandHandler("registro", registro),
        CommandHandler("stato", stato),
        CommandHandler("aiuto", aiuto),
        CommandHandler("help", aiuto),
        CommandHandler("ping", ping),
        CommandHandler("annulla", cmd_annulla_idle),
    ]
