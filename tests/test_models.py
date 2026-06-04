from docrt.models import ErrorCode, ExitCode, Result, exit_code_for_result


def test_result_shape_has_fixed_fields():
    result = Result(
        ok=True,
        operation="doctor",
        input_path=None,
        output_path=None,
        backend="doctor",
        run_id="run",
        started_at="start",
        ended_at="end",
        duration_ms=1,
    )
    assert set(result.to_dict()) == {
        "ok",
        "operation",
        "input_path",
        "output_path",
        "backend",
        "run_id",
        "started_at",
        "ended_at",
        "duration_ms",
        "error_code",
        "error_message",
        "exception_type",
        "traceback",
        "recovery_actions",
        "diagnostic_report_path",
        "log_path",
        "data",
    }


def test_exit_code_mapping():
    result = Result(
        ok=False,
        operation="x",
        input_path=None,
        output_path=None,
        backend=None,
        run_id="run",
        started_at="start",
        ended_at="end",
        duration_ms=1,
        error_code=ErrorCode.FILE_NOT_FOUND.value,
    )
    assert exit_code_for_result(result) == ExitCode.FILE_NOT_FOUND
