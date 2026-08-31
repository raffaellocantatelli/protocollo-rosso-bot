"""/corpo — hacking del corpo senza setta da integratori."""

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot import db, media

CHIUDI = "Esci corpo"

TASTIERA = ReplyKeyboardMarkup(
    [
        ["Sonno", "Luce"],
        ["Movimento", "Misura"],
        ["Integratori", "/palestra"],
        ["/scheda", CHIUDI],
    ],
    resize_keyboard=True,
)

INTRO = """\\
*Corpo — hacking onesto*

Non è Sinclair. Non è un negozio.
Prima un numero, poi un'ipotesi.

Tocca un tasto. Peso e settimane: /palestra.
"""

SCHEDE = {
    "sonno": """\\
*Sonno*

Orario stabile, buio, niente luce bianca forte l'ultima ora.
Caffeina dopo le 15 e schermo a letto prima di qualsiasi integratore.

Numero: ore di sonno, media su 7 notti.
P6: 14 notti con orario fisso e sei ancora a pezzi → medico, non reel.
""",
    "luce": """\\
*Luce*

Mattina: dieci minuti fuori (non nel sole).
Sera: luce calda e bassa.

Questo muove cortisolo e melatonina più di molti stack.
Occhiali blu / lampada 10.000 lux: ipotesi, solo dopo il basale.
""",
    "movimento": """\\
*Movimento*

Fatto: cammino ogni giorno + 2–4 sedute di forza.
La scheda precisa sta in /palestra, non qui.

Numero: sedute fatte in 7 giorni, oppure passi medi.
P6: 30 giorni senza +forza e senza peso/vita che si muove → teatro.
""",
    "misura": """\\
*Misura*

Sì: senza numero l'ottimizzazione è vuota.
No: non basta «un numero a caso per 90 giorni».

Tre numeri, non di più:
1. *Peso* — media di 7 giorni (non un lunedì)
2. *Vita* in cm, stessa ora, a digiuno
3. *Passi* medi, o sedute di forza fatte

Il piano (fascia, bersaglio, settimane, kcal) lo calcola /palestra.
Oggi registri il punto zero con /fuori, tipo:
`peso 82.4 vita 94 passi 6400`

Controllo a *4 settimane*, non solo a 90.
P6: se a metà del tempo di /scheda non hai fatto metà strada, ricalcoli.
Analisi del sangue: solo quelle già prescritte, non uno shopping di lab.
""",
    "integratori": """\\
*Integratori* — ipotesi, non fede

*Se manca (fatto)*
• Vitamina D — analisi basse
• Omega-3 — se non mangi pesce
• Magnesio sera — se il sonno è corto e il medico non vieta

*Sinclair / reel (ipotesi)*
• NMN/NR alzano il NAD; non la vita umana dimostrata
• Resveratrolo, spermidina, fisetina — deboli o topi

*Farmaco*
Metformina, rapamicina, statina, aspirina quotidiana: medico.

Uno alla volta. Una scadenza. Un numero da rivedere.
Se il numero non si muove, cade.
""",
}


async def cmd_corpo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await media.manda(update, "metodo", sempre=False, p=0.5)
    await update.message.reply_text(INTRO, parse_mode=ParseMode.MARKDOWN, reply_markup=TASTIERA)


async def corpo_tasto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    raw = (update.message.text or "").strip()
    if raw == CHIUDI:
        await update.message.reply_text(
            "Uscito dal corpo. /corpo per rientrare.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return True
    chiave = raw.lower()
    testo = SCHEDE.get(chiave)
    if not testo:
        return False
    try:
        db.add_epistemic(
            update.effective_user.id,
            "TECNICO",
            f"scheda corpo: {chiave}",
            source="corpo",
            how_falls="cade se non segue un atto o una misura",
        )
    except Exception:
        pass
    await update.message.reply_text(testo, parse_mode=ParseMode.MARKDOWN)
    return True
