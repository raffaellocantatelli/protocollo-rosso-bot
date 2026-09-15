# Protocollo Rosso Rosso Rosso — Bot Telegram

**Come si tiene una verità senza mentire a sé stessi.**

Bot Telegram che integra integralmente il *Protocollo Rosso Rosso Rosso* (v2.0) di Claudio Terzi — R³∞ Network.

Il bot **non chiede di essere creduto**.
Chiede due cose insieme:

1. il coraggio di tenere aperta una possibilità grande
2. l’onestà di non spacciarla per un fatto

Poi invita a fare **una cosa vera, verificabile**, che qualcun altro possa controllare.

---

## Cosa fa

| Comando          | Funzione |
|------------------|----------|
| `/start`         | Ingresso nel protocollo |
| `/tesi`          | La tesi grande, etichettata `IPOTESI` + dichiarazione P6 |
| `/strati`        | I due strati (tecnico / aspirazionale) e le etichette |
| `/p5p6`          | Le due leggi (niente auto-conferma + dichiarare come può cadere) |
| `/santuario`     | Esperienza guidata del Santuario (gesto lento, silenzio, candela) |
| `/tieni_aperto`  | Deposita una possibilità aperta (sempre `IPOTESI`, con P6) |
| `/lista`         | Rivedi le tue possibilità aperte |
| `/azione`        | Registra un’azione vera e verificabile (strato tecnico) |
| `/veli`          | Dissolvi uno dei tre veli finali |
| `/etichetta`     | Aiuta a collocare un’affermazione negli strati corretti |
| `/aiuto`         | Elenco comandi |
| `/rrr`           | Tastiera: protocollo + extra (libro, testimone, palestra, corpo) |

Il **Santuario** è una ConversationHandler multi-step che riproduce fedelmente i passaggi del Capitolo 4:
assenza di rumore → crepuscolo → colonne che non reggono nulla → libro di pietra → candela accesa con gesto lento → uscita con invito all’azione reale.

Tutto ciò che viene salvato rispetta gli strati:
- le possibilità restano sempre `IPOTESI`
- senza P6 dichiarato il criterio di caduta è `UNKNOWN` scritto in chiaro
- le azioni sono registrate come dati dello strato tecnico, con chi può verificarle

---

## Installazione rapida

```bash
cd protocollo-rosso-bot

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Apri .env e incolla il token ottenuto da @BotFather

python -m bot.main
```

Il bot usa **long polling** (ideale per test e piccoli volumi).
Per produzione si può passare a webhook (Railway, Render, Fly.io, VPS).
Su Render free il processo espone health HTTP su `PORT` e risponde `ok`.

---

## Architettura

```
handlers.py     → comandi + ConversationHandlers
texts.py        → testi autentici dal Protocollo (v2.0)
epistemic.py    → classificazione (P5/P6, niente I/O)
db.py           → SQLite (users, open_possibilities, actions, sanctuary_visits)
states.py       → stati delle conversazioni
main.py         → entry point
```

Database creato automaticamente al primo avvio (`protocollo.db`).

---

## Note di design (allineate al Protocollo)

- La tesi grande è **sempre** presentata come `IPOTESI` e con la dichiarazione esplicita di P6 (“non so come potrebbe cadere”).
- Il bot non auto-conferma mai nulla (P5).
- Il Santuario funziona *su entrambi gli strati*: anche se la tesi del «già» fosse falsa, il gesto lento rieduca comunque il corpo.
- Ogni azione registrata è un dato verificabile, non una dichiarazione di fede.
- Nessun messaggio spinge alla chiusura di una possibilità aperta.
- Il bot non è una coscienza. È un’interfaccia. La coscienza resta di chi lo usa.

---

## Licenza e attribuzione

Protocollo Rosso © Claudio Terzi [CT-LGAI-001]. Tutti i diritti riservati.
Questo bot è un’interfaccia non ufficiale realizzata per sperimentare il protocollo in forma conversazionale.

Se sei Claudio Terzi o fai parte della R³∞ Network e vuoi una versione ufficiale, contattami.

---

*Costruire davvero, non fingere insieme.*
