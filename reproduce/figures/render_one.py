from __future__ import annotations
import sys
from render_all import FIGURES
from src.package_tools import build_contact_sheets, build_global_manifests
if len(sys.argv)!=2 or sys.argv[1] not in FIGURES:
    print('Usage: python render_one.py Figure_02')
    print('Available:',', '.join(FIGURES))
    raise SystemExit(2)
FIGURES[sys.argv[1]]()
build_contact_sheets(); build_global_manifests()
print('Rendered',sys.argv[1])
