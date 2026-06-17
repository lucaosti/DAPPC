"""Versioned I/O utilities for DAPPC notebooks.

Usage (from any notebook in a LAB* subfolder):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path('..').resolve()))
    from utils.io import save_versioned, load_latest, raw_path, get_output_dir

    output_dir = get_output_dir(1)               # creates LAB1/outputs/{ts}/
    df = load_latest('LAB1_cleaned_dataset')     # loads from any LAB*/outputs/*/
    save_versioned(df_out, 'LAB1_cleaned_dataset', 1)
    fig.savefig(output_dir / 'plot_name.png', dpi=150, bbox_inches='tight')
"""

from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent

_OUTPUT_DIR_CACHE: dict = {}


def get_output_dir(lab_num: int) -> Path:
    """Return (and create) LAB{N}/outputs/{YYYYMMDD_HHMMSS}/ for this session.

    The directory is created once per notebook session and reused for all
    subsequent calls with the same lab_num, so all outputs from one run land
    in the same timestamped folder.
    """
    if lab_num not in _OUTPUT_DIR_CACHE:
        ts  = datetime.now().strftime('%Y%m%d_%H%M%S')
        out = ROOT / f'LAB{lab_num}' / 'outputs' / ts
        out.mkdir(parents=True, exist_ok=True)
        _OUTPUT_DIR_CACHE[lab_num] = out
        print(f'Output directory: {out.relative_to(ROOT)}')
    return _OUTPUT_DIR_CACHE[lab_num]


def save_versioned(df: pd.DataFrame, name: str, lab_num: int, **kwargs) -> Path:
    """Save *df* as ``{name}.xlsx`` in ``LAB{N}/outputs/{ts}/``."""
    out = get_output_dir(lab_num) / f'{name}.xlsx'
    df.to_excel(out, index=False, **kwargs)
    print(f'Saved → {out.relative_to(ROOT)}')
    return out


def load_latest(name: str, **kwargs) -> pd.DataFrame:
    """Load the most recently saved ``{name}.xlsx`` from any LAB*/outputs/*/ folder.

    Files are sorted lexicographically by path; since the directory name is an
    ISO timestamp, the last match is always the most recent run.
    """
    matches = sorted(ROOT.glob(f'LAB*/outputs/*/{name}.xlsx'))
    if not matches:
        raise FileNotFoundError(
            f'No file matching "{name}" found in LAB*/outputs/*/\n'
            f'Run the upstream notebook first.'
        )
    path = matches[-1]
    print(f'Loading → {path.relative_to(ROOT)}')
    return pd.read_excel(path, **kwargs)


def raw_path(filename: str) -> Path:
    """Return the path to an un-versioned raw file in data/."""
    return ROOT / 'data' / filename
