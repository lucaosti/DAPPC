#!/usr/bin/env python3
"""Reset the project to a clean state.

Removes all generated files (outputs, pkl, old images, versioned xlsx)
while keeping source code, the raw dataset, and the virtual environment.

Safe to run at any time. Re-executing all notebooks in order recreates
everything this script deletes.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).parent
KEEP_DATA = ROOT / 'data' / 'Dataset_DAPPC_2026.xlsx'


def reset_project(root: Path | None = None, *, verbose: bool = True) -> list[Path]:
    """Remove generated artifacts. Returns the list of removed paths."""
    root = root or ROOT
    keep_data = root / 'data' / 'Dataset_DAPPC_2026.xlsx'
    removed: list[Path] = []

    def remove(p: Path) -> None:
        rel = p.relative_to(root)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        removed.append(p)
        if verbose:
            print(f'Removed  {rel}')

    for d in sorted(root.glob('LAB*/outputs')):
        remove(d)

    for f in sorted(root.glob('LAB2/*.pkl')):
        remove(f)

    imgs = root / 'LAB2' / 'imgs'
    if imgs.exists():
        remove(imgs)

    for f in sorted(root.glob('LAB4/*.png')):
        remove(f)

    data_dir = root / 'data'
    if data_dir.exists():
        for f in sorted(data_dir.glob('*.xlsx')):
            if f != keep_data:
                remove(f)

    if verbose:
        print('\nProject reset complete.')
        if keep_data.exists():
            print(f'Kept: {keep_data.relative_to(root)}')
        else:
            print(f'Kept: {keep_data.relative_to(root)} (not present)')

    return removed


if __name__ == '__main__':
    reset_project()
