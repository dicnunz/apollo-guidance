"""Execute initialized and cold-start controls, then check trace noninterference."""
from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[1]
def main():
    for name,binary,flags in [('bench','runner',[]),('cold','runner',['--cold']),('uninstrumented','runner-uninstrumented',[])]:
        out=ROOT/'results'/name;out.mkdir(exist_ok=True)
        p=subprocess.run([str(ROOT/'build'/binary),str(ROOT/'results/Luminary099.bin'),str(out),*flags],check=True,text=True,capture_output=True)
        (out/'run.txt').write_text(p.stdout);print(name,p.stdout.strip())
    same=(ROOT/'results/bench/io.csv').read_bytes()==(ROOT/'results/uninstrumented/io.csv').read_bytes()
    assert same,'Instrumentation changed flight-program outputs'
    (ROOT/'results/noninterference.json').write_text(json.dumps({'identical_io_with_unmodified_engine':same},indent=2))
    subprocess.run(['python',str(ROOT/'scripts/decode.py')],check=True)
if __name__=='__main__':main()
