from scimap_agent.analysis import suggest_min_occurrences


def test_auto_threshold_matches_current_reference_corpora():
    assert suggest_min_occurrences(80) == 2
    assert suggest_min_occurrences(251) == 5


def test_auto_threshold_has_minimum_of_two():
    assert suggest_min_occurrences(1) == 2
