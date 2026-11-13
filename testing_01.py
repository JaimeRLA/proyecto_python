from collections.abc import Callable
from datetime import datetime
import os
import random
from typing import TypedDict

from testing_common import test_docstring, test_doctests, test_type_hints, check_duplicated_ids


DATAFILE = '2023_nov.csv'
TESTDATAFILE = 'data_test.csv'
TEST_YEAR = 2023
TEST_MONTH = 'nov'

# Reference values computed independently from data_test.csv (November 2023 sample)
EXPECTED_TOTAL_ROWS = 2121
EXPECTED_QUALIFICATION_COUNTS = {'GRAVE': 1008, 'LEVE': 1103, 'MUY GRAVE': 10}
EXPECTED_TOTAL_AMOUNT = 269410.0
EXPECTED_AVERAGE_AMOUNT = 127.02
EXPECTED_COMPLAINANT_COUNTS = {
    'SER': 938,
    'MEDIOS DE CAPTACION DE IMAGEN': 609,
    'POLICIA MUNICIPAL': 518,
    'AGENTES DE MOVILIDAD': 37,
    'SACE': 19,
}
EXPECTED_TOP_LOCATION = ('CALLE ALCALA 51', 70)
# date_time is always built with day=1, and 2023-11-01 is a Wednesday (index 3)
EXPECTED_WEEKDAY_INDEX = 3

# Reference per-hour stats (count, total, mean) computed independently from data_test.csv
EXPECTED_HOURLY_STATS = [
    {'count': 32, 'total': 6070, 'mean': 189.6875},
    {'count': 28, 'total': 4470, 'mean': 159.64285714285714},
    {'count': 15, 'total': 1870, 'mean': 124.66666666666667},
    {'count': 13, 'total': 2290, 'mean': 176.15384615384616},
    {'count': 13, 'total': 3400, 'mean': 261.53846153846155},
    {'count': 20, 'total': 2790, 'mean': 139.5},
    {'count': 14, 'total': 2180, 'mean': 155.71428571428572},
    {'count': 20, 'total': 3810, 'mean': 190.5},
    {'count': 49, 'total': 7830, 'mean': 159.79591836734693},
    {'count': 163, 'total': 18240, 'mean': 111.90184049079754},
    {'count': 177, 'total': 20810, 'mean': 117.57062146892656},
    {'count': 175, 'total': 18880, 'mean': 107.88571428571429},
    {'count': 169, 'total': 20900, 'mean': 123.66863905325444},
    {'count': 206, 'total': 22220, 'mean': 107.86407766990291},
    {'count': 125, 'total': 14380, 'mean': 115.04},
    {'count': 92, 'total': 11360, 'mean': 123.47826086956522},
    {'count': 128, 'total': 16090, 'mean': 125.703125},
    {'count': 153, 'total': 18450, 'mean': 120.58823529411765},
    {'count': 123, 'total': 15970, 'mean': 129.83739837398375},
    {'count': 144, 'total': 17930, 'mean': 124.51388888888889},
    {'count': 130, 'total': 16400, 'mean': 126.15384615384616},
    {'count': 50, 'total': 8300, 'mean': 166.0},
    {'count': 51, 'total': 9530, 'mean': 186.86274509803923},
    {'count': 31, 'total': 5240, 'mean': 169.03225806451613},
]

# Only fines with recorded speed data (VEL_LIMITE/VEL_CIRCULA) contribute here
EXPECTED_MIN_SPEED_EXCESS = 3

def test_generate_sample(gen_sample: Callable):
    def test(size: int):
        ok = False
        max_attempts = 5
        attempts = 0
        random.seed(42)  # Ensure reproducibility
        while not ok and attempts < max_attempts:
            gen_sample(DATAFILE, size)
            n = round(size*100)
            new_file = DATAFILE.replace('.csv', f'_{size:02d}.csv')
            assert new_file in os.listdir(), f"Sample file for {new_file} size {size} not found"
            with open(new_file, 'r') as f:
                header_new = f.readline()
            with open(DATAFILE, 'r') as f:
                header_full = f.readline()
            assert header_new == header_full, f"Header mismatch in {new_file}"
            fullsize = os.path.getsize(DATAFILE)
            samplesize = os.path.getsize(new_file)
            ok = fullsize*size*0.9/100 <= samplesize <= fullsize*size*1.1/100
            attempts += 1
        print("test_gen_sample", size, attempts)
        assert ok, f"Sample size {size} does not match expected size in {new_file}"
        print(f"Sample size {size} OK")

    for size in [1, 2, 5, 10]:
        test(size)

    ok = False
    try:
        gen_sample(DATAFILE, 120)
    except:
        ok = True
    assert ok, "gen_sample should raise an error for size > 1"

    ok = False
    try:
        gen_sample(DATAFILE, -1)
    except:
        ok = True
    assert ok, "gen_sample should raise an error for size < 0"
    print("check ratio values OK")

def test_gen_sample_typehints(gen_sample):
    test_type_hints(gen_sample, {str, int, None})


def test_parse_row(parse_row: Callable):
    row = {
        'CALIFICACION': 'GRAVE',
        'LUGAR': 'CALLE MAYOR',
        'HORA': '17.37',
        'IMP_BOL': ' 200.00',
        'DENUNCIANTE': 'AGENTES DE MOVILIDAD',
        'VEL_CIRCULA ': '   ',
        'VEL_LIMITE': '   '
    }
    result = parse_row(row, 2023, 'nov')
    assert result['date_time'] == datetime(2023, 11, 1, 17, 37), \
        f"Expected date_time 2023-11-01 17:37, got {result['date_time']}"
    assert result['qualification'] == 'GRAVE', f"Unexpected qualification: {result['qualification']}"
    assert result['location'] == 'CALLE MAYOR', f"Unexpected location: {result['location']}"
    assert result['complainant'] == 'AGENTES DE MOVILIDAD', f"Unexpected complainant: {result['complainant']}"
    assert result['amount'] == 200, f"Unexpected amount: {result['amount']}"
    assert isinstance(result['amount'], int), f"{result['amount']} is not and integer"
    assert result['speed_limit'] is None, f"Unexpected speed_limit: {result['speed_limit']}"
    assert result['real_speed'] is None, f"Unexpected real_speed: {result['real_speed']}"
    row2 = {
        'CALIFICACION': 'LEVE',
        'LUGAR': 'CALLE MAYOR',
        'HORA': '08.05',
        'IMP_BOL': ' 100.00',
        'DENUNCIANTE': 'SER',
        'VEL_CIRCULA ': '80   ',
        'VEL_LIMITE': '70   '
    }
    result2 = parse_row(row2, 2024, 'jan')
    assert result2['date_time'] == datetime(2024, 1, 1, 8, 5), \
        f"Expected date_time 2024-01-01 08:05, got {result2['date_time']}"
    assert result2['speed_limit'] == 70, f"Unexpected speed_limit: {result2['speed_limit']}"
    assert result2['real_speed'] == 80, f"Unexpected real_speed: {result2['real_speed']}"

    # The raw CSV pads CALIFICACION, LUGAR and DENUNCIANTE with whitespace;
    # parse_row must strip these fields itself, not leave it to callers.
    padded_row = {
        'CALIFICACION': '  GRAVE   ',
        'LUGAR': '  CALLE MAYOR  ',
        'HORA': '09.15',
        'IMP_BOL': ' 90.00',
        'DENUNCIANTE': '  AGENTES DE MOVILIDAD  ',
        'VEL_CIRCULA ': '   ',
        'VEL_LIMITE': '   '
    }
    padded_result = parse_row(padded_row, 2023, 'nov')
    assert padded_result['qualification'] == 'GRAVE', \
        f"qualification must be stripped in parse_row, got {padded_result['qualification']!r}"
    assert padded_result['location'] == 'CALLE MAYOR', \
        f"location must be stripped in parse_row, got {padded_result['location']!r}"
    assert padded_result['complainant'] == 'AGENTES DE MOVILIDAD', \
        f"complainant must be stripped in parse_row, got {padded_result['complainant']!r}"

    print("test_parse_row OK")


def test_parse_row_typehints(parse_row: Callable, TrafficFine):
    test_type_hints(parse_row, {dict[str, str], int, str, TrafficFine})


def test_load_fines_data(load_fines_data: Callable):
    data = load_fines_data(TEST_YEAR, TEST_MONTH, TESTDATAFILE)
    assert isinstance(data, list), "load_fines_data must return a list"
    assert len(data) == EXPECTED_TOTAL_ROWS, \
        f"Expected {EXPECTED_TOTAL_ROWS} records, got {len(data)}"
    first = data[0]
    for key in ('date_time', 'qualification', 'location', 'amount', 'complainant'):
        assert key in first, f"Missing key '{key}' in TrafficFine record"
    assert isinstance(first['date_time'], datetime), "date_time must be a datetime object"
    assert first['date_time'].year == TEST_YEAR
    assert first['date_time'].month == 11
    assert first['date_time'].day == 1

    # data_test.csv pads these columns with whitespace; load_fines_data (via
    # parse_row) must strip them for every record, not just the first one.
    for key in ('qualification', 'location', 'complainant'):
        for record in data:
            assert record[key] == record[key].strip(), \
                f"Field '{key}' must be stripped of whitespace, got {record[key]!r}"

    data = load_fines_data(2023, 'nov')
    try:
        for month in ['ene', 'dic']:
            data = load_fines_data(2023, 'ene')
    except:
        pass
    else:
        raise AssertionError(f'Month not checked: {month}')
    print("test_load_fines_data OK")


def test_load_fines_data_typehints(load_fines_data: Callable, TrafficFine):
    test_type_hints(load_fines_data, {str|None, str, int, list[TrafficFine]})


def test_count_by_qualification(count_by_qualification: Callable, data: list):
    for qualification, expected in EXPECTED_QUALIFICATION_COUNTS.items():
        result = count_by_qualification(data, qualification)
        assert result == expected, \
            f"count_by_qualification(data, '{qualification}') == {result}, expected {expected}"
    # case-insensitivity check
    result_lower = count_by_qualification(data, 'grave')
    assert result_lower == EXPECTED_QUALIFICATION_COUNTS['GRAVE'], \
        "count_by_qualification should be case-insensitive"
    assert count_by_qualification([], 'GRAVE') == 0, "count_by_qualification([], ...) should be 0"
    try:
        count_by_qualification(data, 'gre')
    except:
        pass
    else:
        raise AssertionError('qualifications must be checked')
    print("test_count_by_qualification OK")


def test_count_by_qualification_typehints(count_by_qualification: Callable, traffic_fine_type):
    test_type_hints(count_by_qualification, {list[traffic_fine_type], str, int})


def test_calculate_amount_stats(calculate_amount_stats: Callable, data: list):
    total, average = calculate_amount_stats(data)
    assert total == EXPECTED_TOTAL_AMOUNT, f"Expected total {EXPECTED_TOTAL_AMOUNT}, got {total}"
    assert average == EXPECTED_AVERAGE_AMOUNT, f"Expected average {EXPECTED_AVERAGE_AMOUNT}, got {average}"
    assert calculate_amount_stats([]) == (0.0, 0.0), "calculate_amount_stats([]) should be (0.0, 0.0)"
    print("test_calculate_amount_stats OK")


def test_calculate_amount_stats_typehints(calculate_amount_stats: Callable, traffic_fine_type):
    test_type_hints(calculate_amount_stats, {list[traffic_fine_type], tuple[float, float]})


def test_count_by_complainant(count_by_complainant: Callable, data: list):
    result = count_by_complainant(data)
    for complainant, expected in EXPECTED_COMPLAINANT_COUNTS.items():
        assert result.get(complainant) == expected, \
            f"count_by_complainant(data)['{complainant}'] == {result.get(complainant)}, expected {expected}"
    assert count_by_complainant([]) == {}, "count_by_complainant([]) should be {}"
    print("test_count_by_complainant OK")


def test_count_by_complainant_typehints(count_by_complainant: Callable, traffic_fine_type):
    test_type_hints(count_by_complainant, {list[traffic_fine_type], dict[str, int]})


def test_top_location_fines(top_location_fines: Callable, data: list):
    result = top_location_fines(data)
    assert result == EXPECTED_TOP_LOCATION, \
        f"top_location_fines(data) == {result}, expected {EXPECTED_TOP_LOCATION}"
    print("test_top_location_fines OK")


def test_top_location_fines_typehints(top_location_fines: Callable, traffic_fine_type):
    test_type_hints(top_location_fines, {list[traffic_fine_type], tuple[str, int]})


def test_fines_by_hour(fines_by_hour: Callable, data: list):
    result = fines_by_hour(data)
    assert isinstance(result, list) and len(result) == 24, "Result must be a list of 24 elements"

    total_count = sum(counter['count'] for counter in result)
    total_amount = sum(counter['total'] for counter in result)
    assert total_count == EXPECTED_TOTAL_ROWS, \
        f"Histogram total count {total_count} does not match dataset size {EXPECTED_TOTAL_ROWS}"
    assert total_amount == EXPECTED_TOTAL_AMOUNT, \
        f"Histogram total amount {total_amount} does not match expected {EXPECTED_TOTAL_AMOUNT}"

    for hour, expected in enumerate(EXPECTED_HOURLY_STATS):
        counter = result[hour]
        for key in ('count', 'total', 'mean'):
            assert key in counter, f"Missing key '{key}' in the Counter for hour {hour}"
        assert counter['count'] == expected['count'], \
            f"Hour {hour}: expected count {expected['count']}, got {counter['count']}"
        assert counter['total'] == expected['total'], \
            f"Hour {hour}: expected total {expected['total']}, got {counter['total']}"
        assert abs(counter['mean'] - expected['mean']) < 0.01, \
            f"Hour {hour}: expected mean {expected['mean']}, got {counter['mean']}"

    # An hour with no fines at all must not raise (division by zero) and should be all zeros
    empty_result = fines_by_hour([])
    assert len(empty_result) == 24
    assert all(counter['count'] == 0 and counter['total'] == 0 and counter['mean'] == 0.0
               for counter in empty_result), \
        "An empty dataset must produce 24 zeroed-out counters, without raising ZeroDivisionError"

    print("test_fines_by_hour OK")


def test_fines_by_hour_typehints(fines_by_hour: Callable, traffic_fine_type, counter_type):
    test_type_hints(fines_by_hour, {list[traffic_fine_type], list[counter_type]})


def test_min_speed_excess(min_speed_excess: Callable, data: list):
    result = min_speed_excess(data)
    assert result == EXPECTED_MIN_SPEED_EXCESS, \
        f"Expected min speed excess {EXPECTED_MIN_SPEED_EXCESS}, got {result}"
    assert min_speed_excess([]) == 0, "min_speed_excess([]) should be 0"

    sample = [
        {'speed_limit': 50, 'real_speed': 70},
        {'speed_limit': 30, 'real_speed': 35},
        {'speed_limit': 90, 'real_speed': None},
        {'speed_limit': None, 'real_speed': None},
    ]
    assert min_speed_excess(sample) == 5, \
        f"Expected 5 for the sample data, got {min_speed_excess(sample)}"
    print("test_min_speed_excess OK")


def test_min_speed_excess_typehints(min_speed_excess: Callable, traffic_fine_type):
    test_type_hints(min_speed_excess, {list[traffic_fine_type], int})
