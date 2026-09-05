from pathlib import Path
import subprocess, sys, os

TASKS = [
    ("A tight inset", Path("../../src/ovito/panel_A/16_A_render_final_standalone_linker_inset.py")),
    ("B tight inset", Path("../../src/ovito/panel_B/13_render_B_local_inset_fixed.py")),
    ("C tight inset", Path("../../src/ovito/panel_C/06_C_render_boundary_inset_screen.py")),
    ("D tight inset", Path("../../src/ovito/panel_D/05_D_render_linker_inset_screen.py")),
    ("E tight inset", Path("../../src/ovito/panel_E/08_E_render_linker_inset_screen.py")),
    ("F tight inset", Path("../../src/ovito/panel_F/06_F_render_cyano_inset_screen.py")),
]

def main():
    here=Path(__file__).resolve().parent
    env=os.environ.copy()
    py=sys.executable
    print("="*90)
    print("PROJECT 7B — FINAL TIGHT INSET RERENDER")
    print("="*90)
    for label,rel in TASKS:
        script=here/rel
        print("\n"+"-"*90)
        print("RUNNING:",label)
        print(script)
        print("-"*90)
        subprocess.run([py,script.name],cwd=str(script.parent),env=env,check=True)
    print("\nAll six inset pairs rendered.")
    print("Next: python 30_collect_tight_insets.py")

if __name__=="__main__":
    main()
