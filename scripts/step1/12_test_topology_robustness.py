#!/usr/bin/env python3
"""Step 1b of 5: test results using source-CrystalNet agreement only.

Pairs are retained only when both endpoints have the same topology from the
source label and CrystalNets. Pair construction is not repeated and adsorption
outcomes did not influence this restriction. Direction-free magnitudes are
summarized exactly as in the current main analysis.
"""
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ANALYSIS=ROOT/"analysis"
TOPOLOGY_PAIRS=ANALYSIS/"topology_provenance_pairs.parquet"
EFFECTS=ANALYSIS / "final_primary_pair_effect_magnitudes.parquet"
FULL_CLASS=ANALYSIS/"corrected_pressure_magnitude_summary.csv"
FULL_METAL=ANALYSIS/"unordered_metal_change_pressure_summary.csv"

CLASS_OUT=ANALYSIS/"step1_high_confidence_topology_class_pressure.csv"
METAL_OUT=ANALYSIS/"step1_high_confidence_topology_metal_pressure.csv"
COMPARE_OUT=ANALYSIS/"step1_topology_robustness_comparison.csv"
SUMMARY_OUT=ANALYSIS/"step1_topology_robustness_summary.csv"

N_JOBS=6
BOOTSTRAP_REPLICATES=10_000
BASE_SEED=1701
MIN_METAL_GROUPS=5
MEASURES=["absolute_uptake_difference","absolute_log_difference",
          "absolute_log_difference_sensitivity","standardized_absolute_difference"]


def bootstrap_task(task):
    index, keys, values = task
    rng=np.random.default_rng(BASE_SEED+index)
    values=np.asarray(values,dtype=float)
    draws=np.empty(BOOTSTRAP_REPLICATES)
    for i in range(BOOTSTRAP_REPLICATES):
        draws[i]=np.median(rng.choice(values,size=len(values),replace=True))
    lo,hi=np.quantile(draws,[.025,.975])
    return keys,float(np.median(values)),float(lo),float(hi)


def summarize(group_data, identity):
    tasks=[]; meta=[]; idx=0
    group_cols=[*identity,"target","T/K","p/bar"]
    for keys,g in group_data.groupby(group_cols,sort=False,dropna=False):
        if not isinstance(keys,tuple): keys=(keys,)
        base=dict(zip(group_cols,keys))
        base["groups_of_related_comparisons"]=g["dependence_family_id"].nunique()
        meta.append(base)
        for measure in MEASURES:
            values=g[measure].dropna().to_numpy(float)
            tasks.append((idx,(len(meta)-1,measure),values)); idx+=1
    with ProcessPoolExecutor(max_workers=N_JOBS) as ex:
        results=list(ex.map(bootstrap_task,tasks))
    for (row_index,measure),median,lo,hi in results:
        meta[row_index][f"median_{measure}"]=median
        meta[row_index][f"bootstrap_95_low_{measure}"]=lo
        meta[row_index][f"bootstrap_95_high_{measure}"]=hi
    return pd.DataFrame(meta)


def pressure(summary,identity):
    rows=[]
    for keys,g in summary.groupby([*identity,"target","T/K"],sort=False):
        if not isinstance(keys,tuple): keys=(keys,)
        g=g.sort_values("p/bar")
        if len(g)!=2: raise RuntimeError(f"Expected two pressures for {keys}")
        low,high=g.iloc[0],g.iloc[1]
        row=dict(zip([*identity,"target","T/K"],keys))
        row.update({
          "p/bar_low":low["p/bar"],"p/bar_high":high["p/bar"],
          "groups_low":low["groups_of_related_comparisons"],
          "groups_high":high["groups_of_related_comparisons"],
          "change_in_absolute_log_difference":high["median_absolute_log_difference"]-low["median_absolute_log_difference"],
          "change_in_standardized_absolute_difference":high["median_standardized_absolute_difference"]-low["median_standardized_absolute_difference"],
        })
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    for f in [TOPOLOGY_PAIRS,EFFECTS,FULL_CLASS,FULL_METAL]:
        if not f.exists(): raise FileNotFoundError(f)
    topo=pd.read_parquet(TOPOLOGY_PAIRS)
    keys=["intervention","pair_lo","pair_hi"]
    high=topo.loc[topo["both_endpoints_source_crystalnet_agree"],keys].drop_duplicates()
    effects=pd.read_parquet(EFFECTS)
    selected=high.merge(effects,on=keys,how="left",validate="one_to_many")
    expected=len(high)*18
    if len(selected)!=expected: raise RuntimeError(f"Expected {expected} rows, found {len(selected)}")
    selected=selected.loc[selected["outcome_complete"]].copy()

    # One value per related group and condition.
    agg={m:(m,"median") for m in MEASURES}
    class_group=(selected.groupby(["intervention","dependence_family_id","target","T/K","p/bar"],as_index=False)
                 .agg(**agg))
    class_summary=summarize(class_group,["intervention"])
    class_pressure=pressure(class_summary,["intervention"])
    class_pressure.to_csv(CLASS_OUT,index=False)

    metal=selected.loc[selected["intervention"].eq("metal_substitution")].copy()
    support=metal.groupby("transition")["dependence_family_id"].nunique()
    retained=set(support[support>=MIN_METAL_GROUPS].index)
    metal=metal.loc[metal["transition"].isin(retained)]
    metal_group=(metal.groupby(["transition","dependence_family_id","target","T/K","p/bar"],as_index=False)
                 .agg(**agg))
    metal_summary=summarize(metal_group,["transition"])
    metal_pressure=pressure(metal_summary,["transition"])
    metal_pressure.to_csv(METAL_OUT,index=False)

    full_class=pd.read_csv(FULL_CLASS)
    full_metal=pd.read_csv(FULL_METAL)
    cc=full_class.merge(class_pressure,on=["intervention","target","T/K"],suffixes=("_full","_agreement"),validate="one_to_one")
    cc["analysis_level"]="intervention_class"
    mc=full_metal.merge(metal_pressure,on=["transition","target","T/K"],suffixes=("_full","_agreement"),validate="one_to_one")
    mc["analysis_level"]="exact_unordered_metal_change"
    comparison=pd.concat([cc,mc],ignore_index=True,sort=False)
    comparison["same_log_pressure_direction"]=(np.sign(comparison["change_in_absolute_log_difference_full"])==np.sign(comparison["change_in_absolute_log_difference_agreement"]))
    comparison["same_standardized_pressure_direction"]=(np.sign(comparison["change_in_standardized_absolute_difference_full"])==np.sign(comparison["change_in_standardized_absolute_difference_agreement"]))
    comparison.to_csv(COMPARE_OUT,index=False)
    summary=(comparison.groupby("analysis_level",as_index=False)
             .agg(comparisons=("analysis_level","size"),
                  same_log_pressure_direction=("same_log_pressure_direction","sum"),
                  same_standardized_pressure_direction=("same_standardized_pressure_direction","sum")))
    summary.to_csv(SUMMARY_OUT,index=False)

    print(f"N_JOBS={N_JOBS}; bootstrap_replicates={BOOTSTRAP_REPLICATES}; high_confidence_pairs={len(high):,}; complete_condition_rows={len(selected):,}")
    print("\nTOPOLOGY ROBUSTNESS SUMMARY")
    print(summary.to_string(index=False))
    print("\nHIGH-CONFIDENCE PAIRS BY INTERVENTION")
    print(high["intervention"].value_counts().to_string())
    print("\nRETAINED METAL CHANGES")
    print(metal.groupby("transition")["dependence_family_id"].nunique().sort_values(ascending=False).to_string())
    print("\nOutputs:")
    for f in [CLASS_OUT,METAL_OUT,COMPARE_OUT,SUMMARY_OUT]: print(f)
    print("No pair was selected using adsorption outcomes. Metal changes remained unordered. No missing value was filled.")

if __name__=="__main__": main()

