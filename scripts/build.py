"""Build the original flight program and a passively instrumented yaAGC engine."""
from pathlib import Path
import subprocess,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'vendor/virtualagc';B=ROOT/'build';R=ROOT/'results'
def command(args,cwd=None):subprocess.run(args,cwd=cwd or ROOT,check=True)
def main():
    B.mkdir(exist_ok=True);R.mkdir(exist_ok=True)
    for part,target in [('yaYUL',None),('Tools','oct2bin')]:
        command(['make','-C',str(V/part),*([target] if target else []),'cc=gcc',r'NVER=\"20260909\"'])
    command(['make','cc=gcc',r'NVER=\"20260909\"'],V/'Luminary099')
    compiled=V/'Luminary099/MAIN.agc.bin';reference=V/'Luminary099/Luminary099.bin'
    assert compiled.read_bytes()==reference.read_bytes(),'Assembly differs from reference binsource'
    shutil.copy2(compiled,R/'Luminary099.bin')
    engine=(V/'yaAGC/agc_engine.c').read_text();anchor='  // Now that the index value has been used, get rid of it.'
    assert engine.count(anchor)==1
    instrumented=engine.replace(anchor,'  extern void HamiltonTrace(agc_t *, int, int, int);\n  HamiltonTrace(State, ProgramCounter, Instruction, sExtraCode);\n\n'+anchor)
    (B/'agc_engine.c').write_text(instrumented)
    for name,source in [('runner',B/'agc_engine.c'),('runner-uninstrumented',V/'yaAGC/agc_engine.c')]:
        command(['gcc','-O2','-I'+str(V/'yaAGC'),str(ROOT/'src/runner.c'),str(source),str(V/'yaAGC/agc_engine_init.c'),'-lm','-o',str(B/name)])
    files=['yaAGC/agc_engine.c','yaAGC/agc_engine_init.c','Luminary099/Luminary099.binsource','Luminary099/MAIN.agc.bin']
    (R/'build-manifest.json').write_text(json.dumps({'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=V,text=True).strip(),'reference_binary_matches':True,'binary_bytes':compiled.stat().st_size,'files':{f:hashlib.sha256((V/f).read_bytes()).hexdigest() for f in files}},indent=2))
if __name__=='__main__':main()
