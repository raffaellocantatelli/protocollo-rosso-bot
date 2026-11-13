"""
test_audit.py — Catena di Prova per R3∞ EVIDENCE_CANDIDATE
Tests:
  a. Diff del codice (verifica campi strutturati presenti)
  b. NOP Invariant (ciclo prosegue senza dati)
  c. Fault Isolation (eccezioni non abbattono il ciclo)
  d. Chain-Forwarding (output[n].data -> input[n+1])
  e. Benchmark p50/p95/p99 su 1000+ iterazioni
"""

import sys
import os
import time
import statistics
import uuid
import json
import difflib

sys.path.insert(0, os.path.dirname(__file__))

import r3_system as evolved

ORIGINAL_PATH = os.path.join(os.path.dirname(__file__), 'r3_system_v14_baseline.py')


class TestDiffCodeChanges:
    """Verifica che il codice evoluto contenga i campi strutturati richiesti."""

    def test_schema_version_present(self):
        assert hasattr(evolved, 'SCHEMA_VERSION')
        assert 'EVIDENCE' in evolved.SCHEMA_VERSION

    def test_metadata_fields_in_step(self):
        engine = evolved.CyclicFlowEngine()
        result = engine.step("test_data")
        required_fields = [
            'run_id', 'schema_version', 'epoch', 'hop', 'max_hops',
            'source', 'destination', 'trigger', 'data', 'trace', 'error', 'timestamp'
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_version_bumped(self):
        assert evolved.R3MultiSystem.VERSION == "15.0.0-EVIDENCE"

    def test_diff_exists(self):
        """Verifica differenza reale tra baseline v14 e v15."""
        if not os.path.exists(ORIGINAL_PATH):
            return
        with open(ORIGINAL_PATH) as f:
            original = f.readlines()
        evolved_path = os.path.join(os.path.dirname(__file__), 'r3_system.py')
        with open(evolved_path) as f:
            evolved_lines = f.readlines()
        diff = list(difflib.unified_diff(original, evolved_lines, lineterm=''))
        assert len(diff) > 0, "No diff found — files are identical"


class TestNopInvariant:
    def test_step_nop(self):
        engine = evolved.CyclicFlowEngine()
        result = engine.step()
        assert result["data"] == "NOP"
        assert result["error"] is None
        assert result["epoch"] == 0

    def test_full_cycle_nop(self):
        engine = evolved.CyclicFlowEngine()
        results = engine.full_cycle()
        assert len(results) == 4
        for r in results:
            assert r["data"] == "NOP"
            assert r["error"] is None

    def test_multi_cycle_nop(self):
        engine = evolved.CyclicFlowEngine()
        for _ in range(3):
            results = engine.full_cycle()
            assert len(results) == 4
        assert engine.epoch == 12

    def test_epoch_advances_on_nop(self):
        engine = evolved.CyclicFlowEngine()
        engine.step()
        engine.step()
        assert engine.epoch == 2


class FaultyEngine(evolved.CyclicFlowEngine):
    def __init__(self, fail_at_hop=1):
        super().__init__()
        self.fail_at_hop = fail_at_hop
        self._call_count = 0

    def _process_node(self, transition, data):
        self._call_count += 1
        if (self._call_count - 1) == self.fail_at_hop:
            raise RuntimeError(f"Simulated corruption at node {transition['from']}")
        return data if data is not None else "NOP"


class TestFaultIsolation:
    def test_single_fault_step(self):
        engine = FaultyEngine(fail_at_hop=0)
        result = engine.step("data_in")
        assert result["error"] is not None
        assert result["error"]["type"] == "RuntimeError"
        assert "Simulated corruption" in result["error"]["message"]

    def test_fault_in_full_cycle(self):
        engine = FaultyEngine(fail_at_hop=2)
        results = engine.full_cycle("seed_data")
        assert len(results) == 4
        errors = [r for r in results if r["error"] is not None]
        assert len(errors) == 1
        assert errors[0]["hop"] == 2

    def test_chain_continues_after_fault(self):
        engine = FaultyEngine(fail_at_hop=1)
        results = engine.full_cycle("seed_data")
        assert results[0]["error"] is None
        assert results[0]["data"] == "seed_data"
        assert results[1]["error"] is not None
        assert results[2]["error"] is None
        assert results[3]["error"] is None
        assert len(results) == 4

    def test_epoch_advances_despite_fault(self):
        engine = FaultyEngine(fail_at_hop=0)
        engine.step()
        assert engine.epoch == 1


class TestChainForwarding:
    def test_seed_propagates(self):
        engine = evolved.CyclicFlowEngine()
        results = engine.full_cycle("SEED_42")
        for r in results:
            assert r["data"] == "SEED_42"

    def test_run_id_consistent(self):
        engine = evolved.CyclicFlowEngine()
        results = engine.full_cycle("x")
        run_ids = {r["run_id"] for r in results}
        assert len(run_ids) == 1

    def test_hop_numbers_sequential(self):
        engine = evolved.CyclicFlowEngine()
        results = engine.full_cycle()
        hops = [r["hop"] for r in results]
        assert hops == [0, 1, 2, 3]

    def test_trace_grows(self):
        engine = evolved.CyclicFlowEngine()
        results = engine.full_cycle("data")
        for i, r in enumerate(results):
            assert len(r["trace"]) == i + 1
        final_trace = results[-1]["trace"]
        expected = ["RAFFA-001", "DECOMP-005", "GEN-006", "WAVE-003"]
        assert final_trace == expected

    def test_max_hops_correct(self):
        engine = evolved.CyclicFlowEngine()
        results = engine.full_cycle()
        for r in results:
            assert r["max_hops"] == 4

    def test_source_destination_chain(self):
        engine = evolved.CyclicFlowEngine()
        results = engine.full_cycle()
        for i in range(len(results) - 1):
            assert results[i]["destination"] == results[i + 1]["source"]


class TestBenchmark:
    ITERATIONS = 1200

    def test_benchmark_full_cycle(self):
        engine = evolved.CyclicFlowEngine()
        latencies = []
        for _ in range(self.ITERATIONS):
            t0 = time.perf_counter()
            engine.full_cycle("bench_data")
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)

        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=100)[94]
        p99 = statistics.quantiles(latencies, n=100)[98]
        mean_lat = statistics.mean(latencies)

        report = {
            "iterations": self.ITERATIONS,
            "p50_ms": round(p50, 4),
            "p95_ms": round(p95, 4),
            "p99_ms": round(p99, 4),
            "mean_ms": round(mean_lat, 4),
            "min_ms": round(min(latencies), 4),
            "max_ms": round(max(latencies), 4),
        }
        report_path = os.path.join(os.path.dirname(__file__), 'benchmark_results.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        assert p99 < 50.0, f"p99 latency {p99:.2f}ms exceeds 50ms threshold"
        assert p50 < 5.0, f"p50 latency {p50:.2f}ms exceeds 5ms threshold"

    def test_benchmark_step_isolation(self):
        engine = evolved.CyclicFlowEngine()
        latencies = []
        for _ in range(1000):
            t0 = time.perf_counter()
            engine.step("step_bench")
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)
        p50 = statistics.median(latencies)
        p99 = statistics.quantiles(latencies, n=100)[98]
        assert p99 < 20.0, f"Step p99 {p99:.2f}ms too high"

    def test_benchmark_fault_overhead(self):
        engine_clean = evolved.CyclicFlowEngine()
        t0 = time.perf_counter()
        for _ in range(500):
            engine_clean.full_cycle("data")
        clean_total = time.perf_counter() - t0

        engine_fault = FaultyEngine(fail_at_hop=2)
        t0 = time.perf_counter()
        for _ in range(500):
            engine_fault._call_count = 0
            engine_fault.full_cycle("data")
        fault_total = time.perf_counter() - t0

        ratio = fault_total / clean_total if clean_total > 0 else 999
        assert ratio < 10.0, f"Fault overhead ratio {ratio:.2f}x exceeds 10x threshold"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
