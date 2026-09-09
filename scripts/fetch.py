"""Fetch the exact VirtualAGC source revision used by this experiment."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'vendor/virtualagc'
COMMIT='ebd8695d23bde6eb9f26933ddf244b8d18987f21'
def main():
    if not (V/'.git').exists():
        V.mkdir(parents=True,exist_ok=True)
        for args in [['init'],['remote','add','origin','https://github.com/virtualagc/virtualagc.git'],['fetch','--depth=1','origin',COMMIT],['checkout','--detach',COMMIT]]:subprocess.run(['git',*args],cwd=V,check=True)
    got=subprocess.check_output(['git','rev-parse','HEAD'],cwd=V,text=True).strip()
    if got!=COMMIT:raise RuntimeError(f'Expected {COMMIT}, found {got}; use a separate clean checkout')
    subprocess.run(['git','diff','--exit-code'],cwd=V,check=True)
    print('Verified source revision',got)
if __name__=='__main__':main()
