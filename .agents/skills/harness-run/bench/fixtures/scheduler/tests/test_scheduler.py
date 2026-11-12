import pytest

from scheduler import build_report, parse_jobs, simulate, topological_order


def test_ignores_blank_full_line_and_inline_comments():
    jobs = parse_jobs("""# release pipeline

    fetch duration=2 priority=4 resources=DB:1 depends=- # primary input
    """)
    assert list(jobs) == ["fetch"]
    assert jobs["fetch"].resources == {"DB": 1}


def test_parses_whitespace_around_fields_and_defaults_failures():
    job = parse_jobs(" build   duration=3   priority=2  resources=- depends=- ")["build"]
    assert (job.duration, job.priority, job.fail, job.dependencies) == (3, 2, 0, ())


def test_duplicate_job_raises_value_error():
    with pytest.raises(ValueError, match="duplicate job 'x'"):
        parse_jobs("x duration=1 priority=0\nx duration=2 priority=0")


def test_invalid_or_nonpositive_job_values_raise_value_error():
    for text in ("x duration=0 priority=0", "x duration=1 priority=-1", "x duration=1 priority=0 resources=GPU:0"):
        with pytest.raises(ValueError):
            parse_jobs(text)


def test_dependencies_are_returned_in_topological_order():
    jobs = parse_jobs("c duration=1 priority=0 depends=a\na duration=1 priority=0\nb duration=1 priority=0 depends=a")
    order = topological_order(jobs)
    assert order.index("a") < order.index("b")
    assert order.index("a") < order.index("c")


def test_unknown_dependency_is_rejected():
    with pytest.raises(ValueError, match="unknown dependency 'missing'"):
        topological_order(parse_jobs("x duration=1 priority=0 depends=missing"))


def test_cycle_error_names_members_in_traversal_order():
    jobs = parse_jobs("a duration=1 priority=0 depends=c\nb duration=1 priority=0 depends=a\nc duration=1 priority=0 depends=b")
    with pytest.raises(ValueError, match=r"dependency cycle: a -> c -> b -> a"):
        topological_order(jobs)


def test_duration_and_dependency_boundaries_are_exact():
    jobs = parse_jobs("a duration=2 priority=0\nb duration=3 priority=0 depends=a")
    result = simulate(jobs, workers=1)
    assert result.makespan == 5
    assert result.jobs == {"a": {"start": 0, "end": 2}, "b": {"start": 2, "end": 5}}


def test_independent_jobs_run_in_parallel():
    jobs = parse_jobs("a duration=4 priority=0\nb duration=3 priority=0")
    result = simulate(jobs, workers=2)
    assert result.makespan == 4
    assert result.jobs["a"] == {"start": 0, "end": 4}
    assert result.jobs["b"] == {"start": 0, "end": 3}


def test_priority_descending_selects_next_ready_job():
    jobs = parse_jobs("long duration=2 priority=10\nurgent duration=1 priority=9\nother duration=1 priority=2")
    result = simulate(jobs, workers=1)
    assert result.jobs["urgent"]["start"] == 2
    assert result.jobs["other"]["start"] == 3


def test_equal_priority_uses_earliest_ready_time():
    jobs = parse_jobs("hold duration=2 priority=10\na duration=1 priority=0 depends=early\nb duration=1 priority=0 depends=late\nearly duration=1 priority=10\nlate duration=2 priority=10")
    result = simulate(jobs, workers=1)
    assert result.jobs["a"]["start"] < result.jobs["b"]["start"]


def test_equal_priority_and_ready_time_use_name_ascending():
    jobs = parse_jobs("z duration=1 priority=2\na duration=1 priority=2")
    result = simulate(jobs, workers=1)
    assert result.jobs["a"]["start"] == 0
    assert result.jobs["z"]["start"] == 1


def test_named_resource_serializes_jobs_even_with_two_workers():
    jobs = parse_jobs("a duration=2 priority=0 resources=DB:1\nb duration=2 priority=0 resources=DB:1")
    result = simulate(jobs, workers=2, resources={"DB": 1})
    assert result.makespan == 4


def test_resource_is_released_at_completion_boundary():
    jobs = parse_jobs("a duration=2 priority=0 resources=GPU:1\nb duration=1 priority=0 resources=GPU:1")
    result = simulate(jobs, workers=2, resources={"GPU": 1})
    assert result.jobs["b"]["start"] == 2


def test_job_requires_all_requested_resource_units():
    jobs = parse_jobs("a duration=2 priority=0 resources=CPU:2")
    with pytest.raises(ValueError, match="insufficient resource 'CPU'"):
        simulate(jobs, workers=1, resources={"CPU": 1})


def test_retry_backoff_starts_after_failed_attempt_finishes():
    jobs = parse_jobs("flaky duration=2 priority=0 fail=1\nafter duration=1 priority=0 depends=flaky")
    result = simulate(jobs, workers=1, backoff=3)
    assert result.jobs["flaky"] == {"start": 0, "end": 7}
    assert result.jobs["after"]["start"] == 7


def test_multiple_declared_failures_each_consume_duration_and_backoff():
    jobs = parse_jobs("flaky duration=1 priority=0 fail=2")
    result = simulate(jobs, workers=1, backoff=2)
    assert result.jobs["flaky"] == {"start": 0, "end": 7}


def test_zero_backoff_retries_at_the_failure_completion_time():
    jobs = parse_jobs("flaky duration=2 priority=0 fail=1")
    assert simulate(jobs, workers=1, backoff=0).jobs["flaky"]["end"] == 4


def test_report_contains_makespan_job_times_and_critical_path():
    jobs = parse_jobs("a duration=3 priority=0\nb duration=2 priority=0 depends=a\nc duration=8 priority=0")
    result = simulate(jobs, workers=2)
    report = build_report(jobs, result)
    assert report == {"makespan": 8, "jobs": result.jobs, "critical_path": ["c"]}


def test_critical_path_tie_uses_alphabetically_earliest_predecessor():
    jobs = parse_jobs("z duration=2 priority=0\na duration=2 priority=0\njoin duration=1 priority=0 depends=z,a")
    report = build_report(jobs, simulate(jobs, workers=3))
    assert report["critical_path"] == ["a", "join"]


def test_empty_schedule_has_zero_makespan_and_empty_critical_path():
    report = build_report({}, simulate({}, workers=1))
    assert report == {"makespan": 0, "jobs": {}, "critical_path": []}
