#!/usr/bin/env python3
"""Run the full DAPPC notebook pipeline.

Clears generated artifacts (like reset.py) and executes lab notebooks in
dependency order. Each notebook is run in isolation via ``jupyter nbconvert
--execute --inplace``, so cell outputs are written back to the .ipynb files.

Usage examples::

    python run_pipeline.py --help
    python run_pipeline.py --reset-only
    python run_pipeline.py --run                 # execute all, no reset
    python run_pipeline.py                       # reset then execute all
    python run_pipeline.py --lab 1
    python run_pipeline.py --skip-existing
    python run_pipeline.py --list
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from reset import reset_project

ROOT = Path(__file__).parent

# Notebooks in pipeline order. LAB4 FuzzyLogic_v2 is a student template and
# is excluded; cluster1/cluster4 are the completed implementations.
PIPELINE: list[tuple[int, Path]] = [
    (1, ROOT / 'LAB1' / 'LAB1.1_Data_Cleaning.ipynb'),
    (1, ROOT / 'LAB1' / 'LAB1.2_MVs_Imputation_kNN.ipynb'),
    (1, ROOT / 'LAB1' / 'LAB1.3_MVs_Imputation_Clustering.ipynb'),
    (2, ROOT / 'LAB2' / 'DAPPC_LAB2_SOM.ipynb'),
    (3, ROOT / 'LAB3' / 'DAPPC_LAB3_ACO.ipynb'),
    (4, ROOT / 'LAB4' / 'DAPPC_LAB4_cluster1.ipynb'),
    (4, ROOT / 'LAB4' / 'DAPPC_LAB4_cluster4.ipynb'),
]

# Artifacts used by --skip-existing (any match under LAB*/outputs/*/ is enough).
EXPECTED_OUTPUTS: dict[Path, tuple[str, ...]] = {
    PIPELINE[0][1]: ('LAB1_cleaned_dataset',),
    PIPELINE[1][1]: ('LAB1_knn_imputed_global', 'LAB1_knn_imputed_by_class'),
    PIPELINE[2][1]: (
        'LAB1_clustering_imputed_global',
        'LAB1_clustering_imputed_by_class',
    ),
    PIPELINE[3][1]: ('LAB2_assignments_knn_global_12x12',),
    PIPELINE[4][1]: ('LAB3_selected_features',),
    PIPELINE[5][1]: (),  # cluster1 has no save_versioned artifact
    PIPELINE[6][1]: ('LAB4_fuzzy_rules_cluster3',),
}

DEFAULT_TIMEOUT = 3600  # seconds per notebook


@dataclass
class RunResult:
    notebook: Path
    lab: int
    status: str  # 'ok' | 'skipped' | 'failed'
    detail: str = ''


def discover_notebooks(lab: int | None = None) -> list[tuple[int, Path]]:
    """Return pipeline entries, optionally filtered by lab number."""
    entries = [(n, p) for n, p in PIPELINE if p.exists()]
    if lab is not None:
        entries = [(n, p) for n, p in entries if n == lab]
    return entries


def outputs_exist(names: tuple[str, ...]) -> bool:
    """True when every named artifact exists in some LAB*/outputs/*/ folder."""
    if not names:
        return False
    for name in names:
        if not list(ROOT.glob(f'LAB*/outputs/*/{name}.xlsx')):
            return False
    return True


def should_skip(notebook: Path, skip_existing: bool) -> bool:
    if not skip_existing:
        return False
    names = EXPECTED_OUTPUTS.get(notebook, ())
    return bool(names) and outputs_exist(names)


def clear_notebook_outputs(notebook: Path) -> None:
    """Strip execution counts and outputs from a notebook file."""
    import nbformat

    nb = nbformat.read(notebook, as_version=4)
    for cell in nb.cells:
        if cell.cell_type == 'code':
            cell.outputs = []
            cell.execution_count = None
    nbformat.write(nb, notebook)


def execute_notebook(notebook: Path, *, timeout: int) -> None:
    """Execute a notebook in place using the nbclient API.

    Runs in-process (avoids the ``jupyter nbconvert`` CLI event-loop bug on
    jupyter_core) and writes executed cell outputs back to the .ipynb file.
    Pre-existing outputs are cleared first so stale/invalid outputs cannot
    abort execution.
    """
    import nbformat
    from nbclient import NotebookClient

    nb = nbformat.read(notebook, as_version=4)

    for cell in nb.cells:
        if cell.get('cell_type') == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None

    client = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name='python3',
        resources={'metadata': {'path': str(notebook.parent)}},
    )
    client.execute()
    nbformat.write(nb, notebook)


def run_pipeline(
    *,
    do_reset: bool = False,
    do_run: bool = True,
    lab: int | None = None,
    skip_existing: bool = False,
    clear_notebooks: bool = False,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[RunResult]:
    results: list[RunResult] = []

    if do_reset:
        reset_project(ROOT)

    if clear_notebooks:
        for _, nb in discover_notebooks(lab):
            clear_notebook_outputs(nb)
            print(f'Cleared outputs in {nb.relative_to(ROOT)}')

    if not do_run:
        return results

    notebooks = discover_notebooks(lab)
    if not notebooks:
        print('No notebooks found for the requested selection.')
        return results

    print(f'\nExecuting {len(notebooks)} notebook(s)...\n')
    for lab_num, nb in notebooks:
        rel = nb.relative_to(ROOT)
        if should_skip(nb, skip_existing):
            msg = 'outputs already present'
            print(f'[SKIP]  {rel}  ({msg})')
            results.append(RunResult(nb, lab_num, 'skipped', msg))
            continue

        print(f'[RUN]   {rel}')
        try:
            execute_notebook(nb, timeout=timeout)
            print(f'[OK]    {rel}')
            results.append(RunResult(nb, lab_num, 'ok'))
        except Exception as exc:  # noqa: BLE001 — report any execution failure
            detail = str(exc).strip()
            if len(detail) > 2000:
                detail = detail[:2000] + '\n... (truncated)'
            print(f'[FAIL]  {rel}')
            if detail:
                print(detail)
            results.append(RunResult(nb, lab_num, 'failed', detail))

    ok = sum(1 for r in results if r.status == 'ok')
    skipped = sum(1 for r in results if r.status == 'skipped')
    failed = sum(1 for r in results if r.status == 'failed')
    print(f'\nDone: {ok} ok, {skipped} skipped, {failed} failed')
    return results


def print_pipeline_list() -> None:
    print('DAPPC notebook pipeline (execution order):\n')
    for i, (lab_num, nb) in enumerate(PIPELINE, start=1):
        exists = 'ok' if nb.exists() else 'MISSING'
        names = EXPECTED_OUTPUTS.get(nb, ())
        artifacts = ', '.join(names) if names else '(no tracked artifact)'
        print(f'  {i}. [LAB{lab_num}] {nb.relative_to(ROOT)}  [{exists}]')
        print(f'      outputs: {artifacts}')
    print(
        '\nDependencies: LAB1.1 → LAB1.2/1.3 → LAB2 → LAB3 → LAB4 '
        '(cluster1 & cluster4 can run after LAB3; both need LAB2 assignments '
        'and cluster1 also needs LAB3 features).'
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Reset generated artifacts and/or run DAPPC lab notebooks.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Default behaviour (no flags): reset project artifacts, then '
            'execute all notebooks in order.\n\n'
            'Notebook execution uses ``jupyter nbconvert --execute --inplace``, '
            'which updates cell outputs in the .ipynb files on disk.'
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        '--reset-only',
        action='store_true',
        help='Only clear generated artifacts (same as reset.py); do not run notebooks.',
    )
    mode.add_argument(
        '--run',
        action='store_true',
        help='Execute notebooks without resetting artifacts first.',
    )
    parser.add_argument(
        '--lab',
        type=int,
        choices=[1, 2, 3, 4],
        metavar='N',
        help='Run only notebooks for LAB N (1–4).',
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip notebooks whose expected output xlsx files already exist.',
    )
    parser.add_argument(
        '--clear-notebooks',
        action='store_true',
        help='Clear cell outputs in notebook files (does not remove LAB*/outputs/).',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List pipeline notebooks and exit.',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=DEFAULT_TIMEOUT,
        metavar='SECS',
        help=f'Per-notebook execution timeout (default: {DEFAULT_TIMEOUT}).',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list:
        print_pipeline_list()
        return 0

    if args.reset_only:
        do_reset, do_run = True, False
    elif args.run:
        do_reset, do_run = False, True
    else:
        # Default: full clean pipeline
        do_reset, do_run = True, True

    results = run_pipeline(
        do_reset=do_reset,
        do_run=do_run,
        lab=args.lab,
        skip_existing=args.skip_existing,
        clear_notebooks=args.clear_notebooks,
        timeout=args.timeout,
    )

    if any(r.status == 'failed' for r in results):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
