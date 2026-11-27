import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from research_experiment import lottery_counts, run_experiment, stride_counts


def test_lottery_draws_are_reproducible_for_a_fixed_seed():
    tickets = {"P1": 5, "P2": 3, "P3": 2}
    assert lottery_counts(tickets, 1000, 19) == lottery_counts(tickets, 1000, 19)


def test_stride_tracks_the_target_share_closely():
    result = run_experiment(decisions=10_000, seeds=5)
    assert result["stride"]["max_absolute_share_error"] < 0.002


def test_rejects_nonpositive_ticket_count():
    try:
        stride_counts({"P1": 2, "P2": 0}, 100)
    except ValueError:
        pass
    else:
        raise AssertionError("zero tickets must be rejected")
