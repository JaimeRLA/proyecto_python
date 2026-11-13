from collections.abc import Callable

import numpy as np

from testing_01 import (
    TESTDATAFILE,
    EXPECTED_TOTAL_ROWS,
    EXPECTED_QUALIFICATION_COUNTS,
    EXPECTED_TOTAL_AMOUNT,
    EXPECTED_AVERAGE_AMOUNT,
    EXPECTED_COMPLAINANT_COUNTS,
    EXPECTED_TOP_LOCATION,
    EXPECTED_HOURLY_STATS,
    EXPECTED_MIN_SPEED_EXCESS,
)
from testing_common import test_docstring, test_doctests, test_type_hints, check_duplicated_ids


def test_records_to_array(records_to_array: Callable, data: list):
    arr = records_to_array(data)
    assert isinstance(arr, np.ndarray), "records_to_array must return a numpy array"
    assert arr.dtype.names is not None, "records_to_array must return a structured array (named fields)"
    for field in ('qualification', 'location', 'amount', 'complainant', 'hour',
                  'speed_limit', 'real_speed'):
        assert field in arr.dtype.names, f"Missing field '{field}' in the structured array"
    assert len(arr) == len(data), f"Expected {len(data)} rows, got {len(arr)}"
    assert 0 <= int(arr['hour'][0]) <= 23, "The 'hour' field must be between 0 and 23"

    from datetime import datetime
    sample = [{
        'date_time': datetime(2023, 11, 1, 17, 37),
        'qualification': 'GRAVE', 'location': 'CALLE MAYOR',
        'amount': 200, 'complainant': 'SER',
        'speed_limit': None, 'real_speed': None,
    }]
    sample_arr = records_to_array(sample)
    assert str(sample_arr['qualification'][0]) == 'GRAVE'
    assert int(sample_arr['amount'][0]) == 200
    assert int(sample_arr['hour'][0]) == 17
    assert np.isnan(sample_arr['speed_limit'][0]), \
        "speed_limit should be NaN when the original value was None"
    print("test_records_to_array OK")


def test_records_to_array_typehints(records_to_array: Callable):
    test_type_hints(records_to_array, {list, np.ndarray})


def test_count_by_qualification_np(count_by_qualification_np: Callable, arr):
    for qualification, expected in EXPECTED_QUALIFICATION_COUNTS.items():
        result = count_by_qualification_np(arr, qualification)
        assert result == expected, \
            f"count_by_qualification_np(arr, '{qualification}') == {result}, expected {expected}"
    assert count_by_qualification_np(arr, 'grave') == EXPECTED_QUALIFICATION_COUNTS['GRAVE'], \
        "count_by_qualification_np should be case-insensitive"
    print("test_count_by_qualification_np OK")


def test_count_by_qualification_np_typehints(count_by_qualification_np: Callable):
    test_type_hints(count_by_qualification_np, {np.ndarray, str, int})


def test_amount_stats_np(amount_stats_np: Callable, arr):
    total, average = amount_stats_np(arr)
    assert total == EXPECTED_TOTAL_AMOUNT, f"Expected total {EXPECTED_TOTAL_AMOUNT}, got {total}"
    assert average == EXPECTED_AVERAGE_AMOUNT, f"Expected average {EXPECTED_AVERAGE_AMOUNT}, got {average}"
    small = np.array([(100,), (50,)], dtype=[('amount', 'i8')])
    assert amount_stats_np(small) == (150.0, 75.0)
    print("test_amount_stats_np OK")


def test_amount_stats_np_typehints(amount_stats_np: Callable):
    test_type_hints(amount_stats_np, {np.ndarray, tuple[float, float]})


def test_count_by_complainant_np(count_by_complainant_np: Callable, arr):
    result = count_by_complainant_np(arr)
    assert isinstance(result, dict), "Result must be a dict"
    for complainant, expected in EXPECTED_COMPLAINANT_COUNTS.items():
        assert result.get(complainant) == expected, \
            f"count_by_complainant_np(arr)['{complainant}'] == {result.get(complainant)}, expected {expected}"
    print("test_count_by_complainant_np OK")


def test_count_by_complainant_np_typehints(count_by_complainant_np: Callable):
    test_type_hints(count_by_complainant_np, {np.ndarray, dict})


def test_top_location_fines_np(top_location_fines_np: Callable, arr):
    result = top_location_fines_np(arr)
    assert result == EXPECTED_TOP_LOCATION, \
        f"top_location_fines_np(arr) == {result}, expected {EXPECTED_TOP_LOCATION}"
    print("test_top_location_fines_np OK")


def test_top_location_fines_np_typehints(top_location_fines_np: Callable):
    test_type_hints(top_location_fines_np, {np.ndarray, tuple[str, int]})


def test_fines_by_hour_np(fines_by_hour_np: Callable, arr):
    result = fines_by_hour_np(arr)
    assert len(result) == 24, f"Expected a 24-element result, got length {len(result)}"

    total_count = int(np.sum(result['count']))
    total_amount = float(np.sum(result['total']))
    assert total_count == EXPECTED_TOTAL_ROWS, \
        f"Histogram total count {total_count} does not match dataset size {EXPECTED_TOTAL_ROWS}"
    assert total_amount == EXPECTED_TOTAL_AMOUNT, \
        f"Histogram total amount {total_amount} does not match expected {EXPECTED_TOTAL_AMOUNT}"

    for hour, expected in enumerate(EXPECTED_HOURLY_STATS):
        assert int(result[hour]['count']) == expected['count'], \
            f"Hour {hour}: expected count {expected['count']}, got {result[hour]['count']}"
        assert float(result[hour]['total']) == expected['total'], \
            f"Hour {hour}: expected total {expected['total']}, got {result[hour]['total']}"
        assert abs(float(result[hour]['mean']) - expected['mean']) < 0.01, \
            f"Hour {hour}: expected mean {expected['mean']}, got {result[hour]['mean']}"

    # An hour with no fines must not raise (division by zero) and must be all zeros
    empty_arr = np.array([], dtype=[('hour', 'i4'), ('amount', 'i8')])
    empty_result = fines_by_hour_np(empty_arr)
    assert len(empty_result) == 24
    assert np.all(empty_result['count'] == 0) and np.all(empty_result['total'] == 0) \
        and np.all(empty_result['mean'] == 0.0), \
        "An empty array must produce 24 zeroed-out entries, without raising ZeroDivisionError"

    print("test_fines_by_hour_np OK")


def test_fines_by_hour_np_typehints(fines_by_hour_np: Callable):
    test_type_hints(fines_by_hour_np, {np.ndarray})


def test_min_speed_excess_np(min_speed_excess_np: Callable, arr):
    result = min_speed_excess_np(arr)
    assert result == EXPECTED_MIN_SPEED_EXCESS, \
        f"Expected min speed excess {EXPECTED_MIN_SPEED_EXCESS}, got {result}"

    empty_arr = np.array([(np.nan, np.nan)], dtype=[('speed_limit', 'f8'), ('real_speed', 'f8')])
    assert min_speed_excess_np(empty_arr) == 0, "min_speed_excess_np with no speed data should be 0"

    sample = np.array(
        [(50.0, 70.0), (30.0, 35.0), (90.0, np.nan)],
        dtype=[('speed_limit', 'f8'), ('real_speed', 'f8')]
    )
    assert min_speed_excess_np(sample) == 5, \
        f"Expected 5 for the sample data, got {min_speed_excess_np(sample)}"
    print("test_min_speed_excess_np OK")


def test_min_speed_excess_np_typehints(min_speed_excess_np: Callable):
    test_type_hints(min_speed_excess_np, {np.ndarray, int})
