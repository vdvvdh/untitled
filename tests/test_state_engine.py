from app.tracking.state_engine import Observation, GameState, classify


def test_active_when_focused_and_recent_input():
    obs = Observation(target_process_running=True, target_process_focused=True, idle_seconds=1.0)
    assert classify(obs) == GameState.ACTIVE


def test_background_when_running_but_not_focused():
    obs = Observation(target_process_running=True, target_process_focused=False, idle_seconds=1.0)
    assert classify(obs) == GameState.BACKGROUND


def test_idle_when_past_threshold():
    obs = Observation(target_process_running=True, target_process_focused=True, idle_seconds=999)
    assert classify(obs) == GameState.IDLE


def test_idle_when_session_locked_even_if_recent_input():
    obs = Observation(target_process_running=True, target_process_focused=True, idle_seconds=0, session_locked=True)
    assert classify(obs) == GameState.IDLE


def test_unknown_when_target_not_running():
    obs = Observation(target_process_running=False, target_process_focused=False, idle_seconds=0)
    assert classify(obs) == GameState.UNKNOWN