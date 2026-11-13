from collections.abc import Callable

import pandas as pd

from testing_01 import TESTDATAFILE, EXPECTED_TOTAL_ROWS, EXPECTED_QUALIFICATION_COUNTS
from testing_common import test_docstring, test_doctests, test_type_hints, check_duplicated_ids


EXPECTED_QUALIFICATION_AVERAGES = {'GRAVE': 177.48, 'LEVE': 75.26, 'MUY GRAVE': 750.0}
EXPECTED_TOP5_LOCATIONS = [
    ('CALLE ALCALA 51', 70),
    ('CALLE GRAN VIA 71', 54),
    ('CALLE ATOCHA 125', 40),
    ('M-30 XC K 19,06 CR4', 32),
    ('CTRA. A42 PK 3.9 SENTIDO DECR.', 29),
]
EXPECTED_CATEGORY_COUNTS = {'BAJO': 1359, 'MEDIO': 732, 'ALTO': 30}

def test_load_dataframe(load_dataframe: Callable):
    df = load_dataframe(TESTDATAFILE)
    assert isinstance(df, pd.DataFrame), "load_dataframe must return a pandas DataFrame"
    assert len(df) == EXPECTED_TOTAL_ROWS, f"Expected {EXPECTED_TOTAL_ROWS} rows, got {len(df)}"
    for col in ('CALIFICACION', 'LUGAR', 'IMP_BOL', 'DENUNCIANTE'):
        assert col in df.columns, f"Missing column '{col}'"
    assert set(df['CALIFICACION'].unique()) == set(EXPECTED_QUALIFICATION_COUNTS.keys()), \
        "CALIFICACION values should be stripped of extra whitespace"
    print("test_load_dataframe OK")


def test_load_dataframe_typehints(load_dataframe: Callable):
    test_type_hints(load_dataframe, {str, pd.DataFrame})


def test_average_amount_by_qualification(average_amount_by_qualification: Callable, df):
    result = average_amount_by_qualification(df)
    assert isinstance(result, pd.Series), "Result must be a pandas Series"
    for qualification, expected in EXPECTED_QUALIFICATION_AVERAGES.items():
        assert abs(result[qualification] - expected) < 0.01, \
            f"Expected average {expected} for {qualification}, got {result[qualification]}"
    assert list(result.index) == sorted(result.index, key=lambda q: -result[q]), \
        "Result must be sorted in descending order"
    print("test_average_amount_by_qualification OK")


def test_average_amount_by_qualification_typehints(average_amount_by_qualification: Callable):
    test_type_hints(average_amount_by_qualification, {pd.DataFrame, pd.Series})


def test_top_n_locations(top_n_locations: Callable, df):
    result = top_n_locations(df, 5)
    assert isinstance(result, pd.DataFrame), "Result must be a pandas DataFrame"
    assert list(result.columns) == ['LUGAR', 'count'], f"Unexpected columns: {list(result.columns)}"
    assert len(result) == 5, f"Expected 5 rows, got {len(result)}"
    actual = list(result.itertuples(index=False, name=None))
    assert actual == EXPECTED_TOP5_LOCATIONS, f"Expected {EXPECTED_TOP5_LOCATIONS}, got {actual}"
    print("test_top_n_locations OK")


def test_top_n_locations_typehints(top_n_locations: Callable):
    test_type_hints(top_n_locations, {pd.DataFrame, int})


def test_add_amount_category(add_amount_category: Callable, df):
    n_columns_before = len(df.columns)
    result = add_amount_category(df)
    assert isinstance(result, pd.DataFrame), "Result must be a pandas DataFrame"
    assert 'CATEGORIA_IMPORTE' in result.columns, "Missing column 'CATEGORIA_IMPORTE'"
    assert len(df.columns) == n_columns_before, \
        "add_amount_category must not mutate the original DataFrame in place"
    counts = result['CATEGORIA_IMPORTE'].value_counts().to_dict()
    for category, expected in EXPECTED_CATEGORY_COUNTS.items():
        assert counts.get(category) == expected, \
            f"Expected {expected} '{category}' fines, got {counts.get(category)}"
    sample = pd.DataFrame({'IMP_BOL': [50.0, 100.0, 150.0, 200.0, 300.0]})
    sample_result = add_amount_category(sample)
    assert list(sample_result['CATEGORIA_IMPORTE'].astype(str)) == \
        ['BAJO', 'BAJO', 'MEDIO', 'MEDIO', 'ALTO'], \
        "Unexpected category boundaries (BAJO<=100, 100<MEDIO<=200, ALTO>200)"
    print("test_add_amount_category OK")


def test_add_amount_category_typehints(add_amount_category: Callable):
    test_type_hints(add_amount_category, {pd.DataFrame})


def test_speed_excess_by_location(speed_excess_by_location: Callable, df):
    result = speed_excess_by_location(df, 5)
    assert isinstance(result, pd.DataFrame), "Result must be a pandas DataFrame"
    assert list(result.columns) == ['LUGAR', 'EXCESO_MEDIO'], \
        f"Unexpected columns: {list(result.columns)}"
    assert len(result) == 5, f"Expected 5 rows, got {len(result)}"

    # Independent reference computed from the very same DataFrame fixture
    speeding = df.dropna(subset=['VEL_LIMITE', 'VEL_CIRCULA']).copy()
    speeding['EXCESO'] = speeding['VEL_CIRCULA'] - speeding['VEL_LIMITE']
    expected = speeding.groupby('LUGAR')['EXCESO'].mean().round(2).sort_values(ascending=False).head(5)
    expected_pairs = list(zip(expected.index.tolist(), expected.values.tolist()))
    actual_pairs = list(result.itertuples(index=False, name=None))
    assert actual_pairs == expected_pairs, f"Expected {expected_pairs}, got {actual_pairs}"
    print("test_speed_excess_by_location OK")


def test_speed_excess_by_location_typehints(speed_excess_by_location: Callable):
    test_type_hints(speed_excess_by_location, {pd.DataFrame, int})


def test_qualification_by_complainant_pivot(qualification_by_complainant_pivot: Callable, df):
    result = qualification_by_complainant_pivot(df)
    assert isinstance(result, pd.DataFrame), "Result must be a pandas DataFrame"
    assert not result.isnull().values.any(), \
        "Pivot table must not contain NaNs; missing combinations should be filled with 0"

    # Independent reference computed from the very same DataFrame fixture
    expected = pd.pivot_table(
        df, index='CALIFICACION', columns='DENUNCIANTE',
        values='IMP_BOL', aggfunc='count', fill_value=0
    ).astype(int)
    result_aligned = result.reindex(index=expected.index, columns=expected.columns).astype(int)
    assert result_aligned.equals(expected), "Pivot table values do not match the expected counts"
    print("test_qualification_by_complainant_pivot OK")


def test_qualification_by_complainant_pivot_typehints(qualification_by_complainant_pivot: Callable):
    test_type_hints(qualification_by_complainant_pivot, {pd.DataFrame})
