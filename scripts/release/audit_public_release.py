#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, csv, hashlib, json, re, subprocess, sys
from pathlib import Path

TARGET_BRANCH = "release/paper7b-public"
EXPECTED_ORIGIN = "alimardani76/isogeometric_mof"
MAX_BYTES = 25 * 1024 * 1024

FINAL = {
"figures/main/Figure_01.pdf":"0e676da4c8fd6b3847a2beca6d699b3e322d1f013664147f78fd976b2a915184",
"figures/main/Figure_01.png":"ff77d4724997e2651a8e89871fe98a1be27bc013a3fc25e51041455987deda75",
"figures/main/Figure_02.pdf":"b575aeddff7736820f49b1aa3891e1738fb20fab19f99f799f803f07c7222f08",
"figures/main/Figure_02.png":"86395acacedb9397ddf426bd309790f443f71ccc0cc4231daa243b0d93434359",
"figures/main/Figure_03.pdf":"c72a3766832bc666909216447e7cd87d07c320f0e7254f74b5dd7a0f602e5f56",
"figures/main/Figure_03.png":"409016a700cc29a59617c20185d3a164582a0ec1557d53cea459cdfef6398982",
"figures/main/Figure_04.pdf":"0f287f987716407c16fdf62dd873df3ff810dad0abfa920e272f664822ce39b9",
"figures/main/Figure_04.png":"e923f95f63ae60af362a5a578292bd7e3792300ed035c19c57edcf92794b66f3",
"figures/main/Figure_05.pdf":"64db93251142ad685d4ab357bc4c7d75c588389dd0395d5a1d5dc687ebc2a830",
"figures/main/Figure_06.pdf":"9b50cc35504df722d8f3080a71cd5d47d38cb7c3d9c693ef75860e166586c1ab",
"figures/main/Figure_06.png":"3396deacb568fe979f7b8d122d76bcfbbac3b9a4da54d8706c36aff2a5404906",
"figures/supplementary/Figure_S01_Additional_Controls.pdf":"8209aa3086500c80802efdc9e19b81c4b45922019714dd99d341dcb47e6e3a30",
"figures/supplementary/Figure_S01_Additional_Controls.png":"1a43d0d7754878ad4f6012920b84251f002ad40b3e4e94a9d79968be12aa2c90",
"figures/supplementary/Figure_S02_HOA_Associations.pdf":"404fa758d392657566df3c649c9f46e3d82271049087827d48870550c80765a3",
"figures/supplementary/Figure_S02_HOA_Associations.png":"a807afb921f1ef7529e3f42aa99fdec8e734f94cb6c3b6575131d3c51ce2080f",
"figures/supplementary/Figure_S03_Guest_Pressure_Specificity.pdf":"cce0283f7b98c539382ae641fd7a9548a7008cdb0be9293e5c8e9993be8c5a0d",
"figures/supplementary/Figure_S03_Guest_Pressure_Specificity.png":"8f7c17d546d0671a2d00aee0c71e384404ce9f924876c17030211e076648c0f9",
"figures/supplementary/Figure_S04_Robustness_Geometry_Sensitivity.pdf":"96586da0e5e93ff233763a727eba4755f81a9855c2fbe4a7ed5c5a5ba6bb4a89",
"figures/supplementary/Figure_S04_Robustness_Geometry_Sensitivity.png":"e6b6ba679823edf2db1c95429f4f9b1f5cd0b970a7a490a86d399c3221778bd1",
"figures/supplementary/Figure_S05_Structural_Geometry_Control.pdf":"a01ab3d1c3122f1cff663c9043ac53ffb41083591bc1104968c31cfa172b74ae",
"figures/supplementary/Figure_S05_Structural_Geometry_Control.png":"f9c0614590259673ad9d9d629a636486ab318e05e1ac452a9661fdd4b9b04546",
"figures/supplementary/Figure_S06_RASPA_Eight_Pair_Detail.pdf":"19ef8dfb410cd9fae655f3dcedbe39b4f79433c6257390adca690fa4abad1d69",
"figures/supplementary/Figure_S06_RASPA_Eight_Pair_Detail.png":"8bef057d9717bdfe2468e31531ed88991caa479db214e03319740828c9ad83b5",
"structural_panel/figures/final/Structural_Panel_FINAL.pdf":"64db93251142ad685d4ab357bc4c7d75c588389dd0395d5a1d5dc687ebc2a830",
"structural_panel/figures/final/Structural_Panel_FINAL.pptx":"16616b7a69e7a57f248210666acbadfd6c8cb62ec9fdbb21df6b72cb647d0f16",
}

STALE = [
".release_tmp",
".github/workflows/install-p7b-canonical-figures.yml",
"figures/main/Figure_01.svg","figures/main/Figure_02.svg","figures/main/Figure_03.svg",
"figures/main/Figure_04.svg","figures/main/Figure_06.svg",
]
LOCAL = ("C:\\Users\\", "/home/", "\\Desktop\\", "/mnt/c/Users/")
TEXT = {".md",".txt",".csv",".json",".yml",".yaml",".py",".bat",".tex",".cff",".toml",".ini",".cfg",".sh",".rst"}
SECRETS = [
("private key",re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
("GitHub token",re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
("GitHub fine-grained token",re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
("AWS access key",re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
("OpenAI key",re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b")),
]

def run(cmd,cwd,check=True):
    p=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if check and p.returncode:
        print(p.stdout)
        raise RuntimeError('failed: '+' '.join(cmd))
    return p

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def candidate(repo):
    raw=run(['git','ls-files','-z','--cached','--others','--exclude-standard'],repo).stdout
    return sorted({repo/x for x in raw.split('\0') if x and (repo/x).is_file()})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True)
    a=ap.parse_args()
    repo=Path(a.repo).resolve(); errors=[]; warns=[]
    if not (repo/'.git').is_dir():
        print('FATAL: not a git repo'); return 2
    branch=run(['git','branch','--show-current'],repo).stdout.strip()
    head=run(['git','rev-parse','HEAD'],repo).stdout.strip()
    origin=run(['git','remote','get-url','origin'],repo).stdout.strip()
    print('branch:',branch); print('HEAD:  ',head); print('origin:',origin)
    if branch!=TARGET_BRANCH: errors.append('wrong branch: '+branch)
    if EXPECTED_ORIGIN not in origin: errors.append('unexpected origin: '+origin)

    for rel,expected in FINAL.items():
        p=repo/rel
        if not p.is_file(): errors.append('missing final asset: '+rel)
        elif sha(p)!=expected: errors.append('SHA-256 mismatch: '+rel)
    for rel in STALE:
        if (repo/rel).exists(): errors.append('stale path still exists: '+rel)

    tracked=set(run(['git','ls-files','-z'],repo).stdout.split('\0'))
    for p in candidate(repo):
        rel=p.relative_to(repo).as_posix(); low=rel.lower()
        if rel in tracked:
            if low.endswith(('.pyc','.zip','.tar.gz')): errors.append('forbidden tracked artifact: '+rel)
            if p.stat().st_size>MAX_BYTES: errors.append('tracked file >25MiB: '+rel)
        if p.suffix.lower() not in TEXT: continue
        try: text=p.read_text(encoding='utf-8-sig')
        except UnicodeDecodeError: continue
        try:
            if p.suffix.lower()=='.py': ast.parse(text,filename=rel)
            elif p.suffix.lower()=='.json': json.loads(text)
            elif p.suffix.lower()=='.csv' and p.stat().st_size:
                with p.open('r',encoding='utf-8-sig',newline='') as f:
                    for _ in csv.reader(f): pass
        except Exception as e:
            errors.append(f'parse/read failure: {rel}: {e}')
        for label,pat in SECRETS:
            if pat.search(text): errors.append(f'possible {label} in {rel}')
        if any(m in text for m in LOCAL):
            if rel=='README.md' or rel.startswith(('archive/','environment/','figures/','provenance/','validation/','structural_panel/','reproduce/')):
                errors.append('local workstation path marker in public/canonical file: '+rel)
            else:
                warns.append('historical local-path assumption retained: '+rel)

    rp=repo/'validation/raspa/data/reproducibility/RASPA_CLOSURE_RUN_AUDIT.csv'
    if not rp.is_file(): errors.append('missing RASPA closure audit')
    else:
        with rp.open('r',encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
        if len(rows)!=192: errors.append(f'RASPA rows {len(rows)} != 192')
        if len({r['job_id'] for r in rows})!=192: errors.append('RASPA job_id not 192 unique')
        if len({r['random_seed'] for r in rows})!=192: errors.append('RASPA random_seed not 192 unique')
        if {r['status'] for r in rows}!={'PASS'}: errors.append('RASPA status not all PASS')
        if {r['raspa_version'] for r in rows}!={'RASPA 3.0.29'}: errors.append('RASPA version mismatch')
        if {r['mode'] for r in rows}!={'henry_full','henry_chargeoff','gcmc_0p1bar','gcmc_1bar'}: errors.append('RASPA mode set mismatch')
        if any(abs(float(r['vdw_cutoff_A'])-12)>1e-12 for r in rows): errors.append('RASPA vdW cutoff mismatch')
        if any(abs(float(r['ewald_precision'])-1e-6)>1e-15 for r in rows): errors.append('RASPA Ewald precision mismatch')
        if {r['coulomb_cutoff_mode'] for r in rows}!={'auto'}: errors.append('RASPA Coulomb cutoff must be auto')
        if any(r['output_hash_matches_archive'].lower() not in ('true','1') for r in rows): errors.append('RASPA output/archive hash mismatch present')

    req=['reproduce/figures/environment.yml','reproduce/figures/requirements.txt','reproduce/figures/render_all.py',
         'reproduce/figures/render_one.py','provenance/final_publication_asset_hashes.csv',
         '.github/workflows/release-integrity.yml','scripts/release/check_repository_integrity.py']
    for rel in req:
        if not (repo/rel).is_file(): errors.append('required release file missing: '+rel)

    docs='\n'.join((repo/p).read_text(encoding='utf-8-sig') for p in ['README.md','figures/README.md','scripts/README.md','reproduce/figures/README.md'] if (repo/p).is_file())
    stale_phrases=['remain to be reconciled before release','historical outputs remain until the finalized','The public-release work will add a smaller Tier-1 publication-reproduction layer','waiting for authoritative packet']
    for phrase in stale_phrases:
        if phrase in docs: errors.append('stale release documentation: '+phrase)
    rr=(repo/'reproduce/figures/README.md').read_text(encoding='utf-8-sig') if (repo/'reproduce/figures/README.md').is_file() else ''
    for bat in ('RUN_ALL_WINDOWS.bat','RUN_MAIN_WINDOWS.bat','RUN_SI_WINDOWS.bat'):
        if bat in rr and not (repo/'reproduce/figures'/bat).exists(): errors.append('README references nonexistent '+bat)

    if run(['git','diff','--cached','--quiet'],repo,check=False).returncode!=0:
        errors.append('index already contains staged changes; deep audit will not alter staging')
    else:
        try:
            run(['git','add','-A'],repo)
            chk=run([sys.executable,'scripts/release/check_repository_integrity.py'],repo,check=False)
            print('\nExisting repository integrity checker:\n'+chk.stdout.rstrip())
            if chk.returncode: errors.append('existing repository integrity checker failed')
        finally:
            run(['git','reset'],repo)

    if not any((repo/x).is_file() for x in ('LICENSE','LICENSE.md','LICENSE.txt')):
        warns.append('LICENSE unresolved/absent — do not invent one before source-rights/code-data decision')
    if not any((repo/x).is_file() for x in ('CITATION.cff','CITATION.md','CITATION')):
        warns.append('CITATION metadata not yet frozen')
    warns += [
        'clean-clone + fresh-environment reproduction test still required',
        'external persistent identifier for multi-GB RASPA raw closure still open if required',
        'repository-wide SHA-256 release manifest must be generated LAST',
        'do not merge/tag/make public until final gates are approved',
    ]

    print('\nWARNINGS / OPEN GATES')
    for x in sorted(set(warns)): print(' WARN:',x)
    print('\nERRORS')
    if errors:
        for x in sorted(set(errors)): print(' ERROR:',x)
        print(f'\nDEEP AUDIT FAILED: {len(set(errors))} hard issue(s)')
        print('Nothing committed. Nothing pushed.')
        return 1
    print(' none')
    print('\nDEEP AUDIT PASS')
    print('No detected hard release-integrity error in the candidate tree.')
    print('Nothing committed. Nothing pushed.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
