import asyncio
import os
import time

from app.healthcheck import heartbeat_loop, heartbeat_path, is_alive


def test_no_heartbeat_file_means_unhealthy(tmp_path):
    assert is_alive(tmp_path / "missing") is False


def test_a_fresh_heartbeat_is_healthy_and_an_old_one_is_not(tmp_path):
    beat = tmp_path / "beat"
    beat.touch()
    assert is_alive(beat) is True
    old = time.time() - 600
    os.utime(beat, (old, old))
    assert is_alive(beat) is False
    assert is_alive(beat, max_age=1000) is True


def test_the_path_can_be_chosen_with_an_environment_variable(tmp_path, monkeypatch):
    monkeypatch.setenv("HEARTBEAT_FILE", str(tmp_path / "custom"))
    assert heartbeat_path() == tmp_path / "custom"


async def test_the_heartbeat_loop_touches_the_file(tmp_path):
    beat = tmp_path / "beat"
    task = asyncio.create_task(heartbeat_loop(beat, interval=0.01))
    await asyncio.sleep(0.05)
    task.cancel()
    assert beat.exists() and is_alive(beat, max_age=5)
