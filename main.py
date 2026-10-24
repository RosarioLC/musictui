import sys

sys.stdout.reconfigure(line_buffering=True)
from ui.app import MusicTUI

try:
    app = MusicTUI()
    app.run()
except Exception as e:  # noqa: BLE001
    print(f"CRASH: {e}", flush=True)
    import traceback

    traceback.print_exc(file=sys.stdout, flush=True)
