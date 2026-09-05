from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))

from src.main_figures import render_all_main, render_figure_01, render_figure_02, render_figure_03, render_figure_04, render_figure_06
from src.si_figures import render_all_si, render_s01, render_s02, render_s03, render_s04, render_s05, render_s06
from src.package_tools import build_contact_sheets, build_global_manifests

FIGURES={
    'Figure_01':render_figure_01,
    'Figure_02':render_figure_02,
    'Figure_03':render_figure_03,
    'Figure_04':render_figure_04,
    'Figure_06':render_figure_06,
    'Figure_S01':render_s01,
    'Figure_S02':render_s02,
    'Figure_S03':render_s03,
    'Figure_S04':render_s04,
    'Figure_S05':render_s05,
    'Figure_S06':render_s06,
}

def main():
    ap=argparse.ArgumentParser(description='Regenerate Paper 7B main + SI quantitative figures from frozen source tables.')
    ap.add_argument('--set',choices=['all','main','si'],default='all')
    ap.add_argument('--only',choices=list(FIGURES),default=None)
    args=ap.parse_args()
    if args.only:
        FIGURES[args.only]()
    elif args.set=='main':
        render_all_main()
    elif args.set=='si':
        render_all_si()
    else:
        render_all_main(); render_all_si()
    build_contact_sheets()
    build_global_manifests()
    print('\nDONE. PDFs and 200-dpi PNGs are in outputs/main and outputs/si.')
    print('Figure 05 is intentionally not regenerated: keep your finalized structural panel.')

if __name__=='__main__':
    main()
