from pathlib import Path
import os, shutil, csv

def detect_root():
    env = os.environ.get("P7B_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if not p.exists():
            raise SystemExit(f"P7B_ROOT is set but does not exist: {p}")
        return p
    return Path(__file__).resolve().parents[2]


def main():
    root=detect_root()
    src=root/"OVITO_screening"
    dst=root/"OVITO_final_insets_tight"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    mapping=[
        ("A","70_A_final_inset_tight/NITRO_plusZn_face__A_i.png","A_i_inset_TIGHT_3200x2400_600dpi.png"),
        ("A","70_A_final_inset_tight/NITRO_plusZn_face__A_ii.png","A_ii_inset_TIGHT_3200x2400_600dpi.png"),
        ("B","70_B_final_inset_tight/D2_ab_plus__B_i_Zn.png","B_i_inset_TIGHT_3200x2400_600dpi.png"),
        ("B","70_B_final_inset_tight/D2_ab_plus__B_ii_Cu.png","B_ii_inset_TIGHT_3200x2400_600dpi.png"),
        ("C","70_C_final_inset_tight/CARBOXY_face__C_i_Zn.png","C_i_inset_TIGHT_3200x2400_600dpi.png"),
        ("C","70_C_final_inset_tight/CARBOXY_face__C_ii_Cu.png","C_ii_inset_TIGHT_3200x2400_600dpi.png"),
        ("D","70_D_final_inset_tight/CTX2_ac_mixed__D_i_ethyl.png","D_i_inset_TIGHT_3200x2400_600dpi.png"),
        ("D","70_D_final_inset_tight/CTX2_ac_mixed__D_ii_methyl.png","D_ii_inset_TIGHT_3200x2400_600dpi.png"),
        ("E","70_E_final_inset_tight/Nfam_face__E_i.png","E_i_inset_TIGHT_3200x2400_600dpi.png"),
        ("E","70_E_final_inset_tight/Nfam_face__E_ii.png","E_ii_inset_TIGHT_3200x2400_600dpi.png"),
        ("F","70_F_final_inset_tight/DIST_D3_face__F_i.png","F_i_inset_TIGHT_3200x2400_600dpi.png"),
        ("F","70_F_final_inset_tight/DIST_D3_face__F_ii.png","F_ii_inset_TIGHT_3200x2400_600dpi.png"),
    ]

    rows=[]; missing=[]
    for panel,rel,name in mapping:
        s=src/rel
        d=dst/panel/name
        d.parent.mkdir(parents=True,exist_ok=True)
        if not s.exists():
            missing.append(str(s)); continue
        shutil.copy2(s,d)
        rows.append({"panel":panel,"source":str(s),"output":str(d)})
        print("copied:",d)

    if missing:
        print("\nMissing expected files:")
        for m in missing: print("  -",m)
        raise SystemExit(1)

    with (dst/"tight_inset_manifest.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["panel","source","output"])
        w.writeheader(); w.writerows(rows)

    print("\nFinal tight-inset folder:",dst)

if __name__=="__main__":
    main()
