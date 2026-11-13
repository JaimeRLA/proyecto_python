from collections.abc import Callable
import doctest
import io
import json
import sys


def test_doctests(fun, globals):
    finder = doctest.DocTestFinder()
    doctests = finder.find(fun)[0].examples
    assert len(doctests) > 0, 'No doctests found in the function'
    out = io.StringIO()
    stdout = sys.stdout
    try:
        sys.stdout = out
        doctest.run_docstring_examples(fun, globals)
    finally:
        sys.stdout = stdout
    assert len(out.getvalue()) == 0, f"Doctest output:\n{out.getvalue()}"
    print("doctests OK")


def test_docstring(fun):
    assert fun.__doc__, 'The function does not have a docstring'
    assert len(fun.__doc__) > 30, 'The docstring is too short'
    print("docstring OK")


def test_type_hints(function: Callable, annotations: set) -> None:
    assert function.__annotations__, f'The function {function.__name__} does not have type hints'
    assert set(function.__annotations__.values()) == annotations, f'type hints expected: {annotations}\n type hints obainted: function.__annotations__.values()'
    print("check type hints OK")


def check_duplicated_ids(notebook_name: str) -> None:
    """Checks that a notebook has no duplicated nbgrader grade_id values.

    This usually happens when a student copies a solution or test cell
    instead of writing their own, dragging its nbgrader metadata along.

    Args:
        notebook_name (str): Path to the .ipynb file to check (e.g.
            'E1_analisis_fichero.ipynb').
    """
    with open(notebook_name, encoding='utf-8') as f:
        nb = json.load(f)

    seen = {}
    duplicates = {}
    for i, cell in enumerate(nb['cells']):
        grade_id = cell.get('metadata', {}).get('nbgrader', {}).get('grade_id')
        if grade_id is None:
            continue
        if grade_id in seen:
            duplicates.setdefault(grade_id, [seen[grade_id]]).append(i)
        else:
            seen[grade_id] = i

    if duplicates:
        print("""ATENCIÓN: hay identificadores de celda duplicados. Esto suele pasar
      al copiar una celda de solución o de test en vez de escribir en la")
      tuya propia. Debes borrar la copia sobrante antes de entregar:
""")
        for grade_id, cell_indices in duplicates.items():
            print(f"   - '{grade_id}' aparece en las celdas: {cell_indices}")
        raise AssertionError("Hay grade_id duplicados. Corrígelo antes de entregar el cuaderno.")
    else:
        print("OK. No se han encontrado grade_id duplicados.")
