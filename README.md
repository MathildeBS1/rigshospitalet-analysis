# rigshospitalet-analysis

## Tutorials

1. Drop `completed_operations.csv` and `cancelled_operations.csv` into `data/`
2. Run `uv sync` to install dependencies
3. Run any script: `uv run python eda/linus/delay_cascade.py`

## How-to guides

**Load data in a notebook:**

```python
import sys; sys.path.insert(0, "src")
from data.loader import load_completed, load_cancelled
df = load_completed()
```

**Add your own analysis:** create a file under `eda/<your-name>/`.

## Explanation

`src/` contains shared modules installed as packages via the build system (`uv sync`), so imports like `from data.loader import load_completed` work from any script or notebook without path hacks.
