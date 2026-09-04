# ERRATA — non usare il Sommario Esecutivo come fonte

Data: 4 settembre 2026. Autore di questa nota: Grok.
Fonte della correzione: codice `bot/sdq1.py` di *questo* repo + tree pubblico `claudioterzi/Claudio` (HEAD `edd84be`, 1 set 2026) + documento di errata del 4 set.

## FATTO (questo bot, protocollo-rosso-bot)

- Non gira la pipeline a sei agenti.
- `GET /sdq1/health` dichiara `agenti: 0`, `ponte_sdq1: assente` se manca `SDQ1_URL`.
- Non esistono qui `agenti.py`, `orchestrator.py` in root, né `--prompt` / `--curl`.
- `/sdq` etichetta un testo (classificatore locale). Punto.

## FATTO (repo claudioterzi/Claudio, letto oggi)

- Entry: `python -m sdq1` → `sdq1/__main__.py` esiste.
- `sdq1/config/sdq1.yaml` esiste.
- `sdq1/sar/agenti_autonomi.py` esiste.
- `sdq1/agents/eternal_backup_agent.py` esiste (l'errata lo dice simulato: non l'ho rieseguito oggi).
- File `agenti.py` in root: **non trovato** dalla ricerca codice.
- Stargazer sul repo: **2** (API GitHub, oggi).

## NON FATTO / NON TOCCATO DA QUI

- Merge del branch `fix-bloccanti`: non l'ho fatto. Non ho verificato se il branch esiste ancora su HEAD settembre.
- PDF *Sommario Esecutivo* su claude.ai: solo Claudio lo rinomina o lo toglie.
- P5/P6 collegati alle ipotesi generate dalla SAR: non patchato alla cieca.

## Regola

Un PDF eloquente non è RECUPERATO. RECUPERATO = file nel tree o output di un comando.
