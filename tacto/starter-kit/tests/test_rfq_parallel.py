"""RFQ timing: every bidder must get its answer within 60 s of its own reply.

Live P05 (f8604d43d3fbf92f) lost threads to timeouts: play() answered one bidder, waited up to a
minute for that bidder's reply, and only then answered the next - whose 60 s had run out. Here the
simulator runs on a scaled clock (1 real second = 60 arena seconds) and every supplier needs
LATENCY to reply, as real ones do ("up to about a minute"), so a sequential loop times out.
"""

import socket
import threading
import time

import pytest

from arena_kit import ArenaClient, RemoteTable, play
from arena_kit.agents.noidea import NoIdeaAgent

SCALE = 60.0  # arena seconds per real second
LATENCY = 66.0  # arena seconds a supplier takes to reply


class ScaledClock:
    def __init__(self):
        self.t0, self.m0 = 1_000_000.0, time.monotonic()

    def __call__(self):
        return self.t0 + (time.monotonic() - self.m0) * SCALE


@pytest.fixture
def slow_sim():
    pytest.importorskip("fastapi")
    import uvicorn

    from arena_kit.sim import Sim, create_app, load_cases

    clock = ScaledClock()
    state = Sim(load_cases(), clock=clock)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(state), port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    yield f"http://127.0.0.1:{port}", state, clock
    server.should_exit = True
    thread.join()


def slow_table(client, state, clock):
    """A table whose suppliers take LATENCY to answer: the reply (and its 60 s clock) starts then."""
    table = RemoteTable(client)
    real_send = table.send

    def send(supplier_id, message):
        reply = real_send(supplier_id, message)
        th = state.sessions[table.session_id]["threads"].get(supplier_id)
        if th is not None:
            th["last_at"] = clock() + LATENCY  # its 60 s start when its reply arrives
        time.sleep(LATENCY / SCALE)
        return reply

    table.send = send
    return table


def test_every_rfq_bidder_is_answered_in_time(slow_sim):
    url, state, clock = slow_sim
    client = ArenaClient(url, ArenaClient(url).register("rfq-timing", "sim")["api_key"], rate=1000)
    table = slow_table(client, state, clock)
    result = play(table, "case:S02", NoIdeaAgent(None))
    s = state.sessions[table.session_id]
    timeouts = {sup: th["timeouts"] for sup, th in s["threads"].items()}
    assert result["ended"] and result["deal"], result
    assert sum(timeouts.values()) == 0, f"bidders timed out: {timeouts}"
