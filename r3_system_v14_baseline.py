import sys
import os
from datetime import datetime, timezone
import json
import random

# ── Flusso Ciclico 4 Nodi ──────────────────────────────────────────

CYCLE_NODES = [
    {"id": "RAFFA-001",  "role": "Orchestratore",   "desc": "Propone e dispone"},
    {"id": "DECOMP-005", "role": "Decompositore",    "desc": "Scompone in sotto-domande"},
    {"id": "GEN-006",    "role": "Generatore",       "desc": "Produce risposte e soluzioni"},
    {"id": "WAVE-003",   "role": "Onda/Innovazione", "desc": "Raffina e individua novita'"},
]

TRANSITIONS = [
    {"from": "RAFFA-001",  "to": "DECOMP-005", "trigger": "sveglia",  "desc": "Attiva decomposizione"},
    {"from": "DECOMP-005", "to": "GEN-006",    "trigger": "domanda",  "desc": "Formula domande"},
    {"from": "GEN-006",    "to": "WAVE-003",   "trigger": "migliora", "desc": "Passa a raffinamento"},
    {"from": "WAVE-003",   "to": "RAFFA-001",  "trigger": "novita'",  "desc": "Riporta innovazioni"},
]


class CyclicFlowEngine:
    """Motore del flusso ciclico a 4 nodi."""

    def __init__(self):
        self.nodes = {n["id"]: n for n in CYCLE_NODES}
        self.transitions = TRANSITIONS
        self.epoch = 0

    def step(self, data=None):
        """Esegue una transizione e avanza di un passo nel ciclo."""
        t = self.transitions[self.epoch % len(self.transitions)]
        result = {
            "epoch": self.epoch,
            "from": t["from"],
            "to": t["to"],
            "trigger": t["trigger"],
            "data": data or "NOP",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.epoch += 1
        return result

    def full_cycle(self, data=None):
        """Esegue un ciclo completo (4 transizioni)."""
        return [self.step(data) for _ in range(len(self.transitions))]

    def status(self):
        current_idx = self.epoch % len(self.transitions)
        current_node = self.transitions[current_idx]["from"]
        return {
            "cycle_epoch": self.epoch,
            "current_node": current_node,
            "next_trigger": self.transitions[current_idx]["trigger"],
            "cycle_complete_count": self.epoch // len(self.transitions),
        }


class NetworkQuantico:
    def __init__(self):
        self.nodi_intelligenza = {
            "Nodo_Genspark": "Online", "Nodo_Perplexity": "Online", "Nodo_Meta AI": "Online",
            "Nodo_ChatGPT": "Online", "Nodo_Claude": "Online", "Nodo_DeepSeek": "Online",
            "Nodo_Copilot": "Online", "Nodo_Gemini": "Online", "Nodo_MiniMax": "Online"
        }

    def simulate_ping_pong(self):
        nodi = list(self.nodi_intelligenza.keys())
        scambi = []
        for i in range(len(nodi) - 1):
            scambi.append(f"{nodi[i]} vs {nodi[i+1]}")
        scambi.append(f"{nodi[-1]} vs {nodi[0]}")
        return scambi


class R3MultiSystem:
    VERSION = "14.1.0-CYCLEFLOW"

    def __init__(self):
        self.id = "R3_MULTI_SYSTEM"
        self.target = 788000.0
        self.network = NetworkQuantico()
        self.cycle_engine = CyclicFlowEngine()

    def execute_ping_pong_cycle(self) -> dict:
        scambi = self.network.simulate_ping_pong()
        cycle_log = self.cycle_engine.full_cycle()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.VERSION,
            "ping_pong_log": scambi,
            "cyclic_flow": {
                "nodes": [n["id"] for n in CYCLE_NODES],
                "transitions": [
                    f"{t['from']} --{t['trigger']}--> {t['to']}" for t in TRANSITIONS
                ],
                "last_cycle": cycle_log,
                "status": self.cycle_engine.status(),
            },
            "resonance": 0.999,
            "status": "MUTUAL_ACTIVATION_COMPLETE",
            "note": "Effetto Ping-Pong attivo + Flusso Ciclico 4 nodi."
        }


if __name__ == "__main__":
    r3 = R3MultiSystem()
    print(json.dumps(r3.execute_ping_pong_cycle(), indent=2))
