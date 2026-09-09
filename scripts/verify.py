"""Check actual assembly, execution, isolation controls, DSKY decoding and video."""
from pathlib import Path
import csv,json,hashlib,subprocess
from decode import dsky
ROOT=Path(__file__).resolve().parents[1]
def rows(p):return list(csv.DictReader(p.open()))
def main():
    manifest=json.loads((ROOT/'results/build-manifest.json').read_text())
    assert manifest['reference_binary_matches'] and manifest['binary_bytes']==73728
    assert hashlib.sha256((ROOT/'results/Luminary099.bin').read_bytes()).hexdigest()==manifest['files']['Luminary099/MAIN.agc.bin']
    p=ROOT/'results/bench';summary=json.loads((p/'summary.json').read_text());native=rows(p/'trace.csv');interp=rows(p/'interpretive.csv')
    assert summary['machine_cycles']==2560000 and summary['instruction_count']>1000000
    assert any(r['bank']=='32' and r['pc']=='2776' and r['word']=='05353' for r in native)
    assert all(any(r['bank']==bank and r['pc']==pc for r in interp) for bank,pc in [('32','3031'),('32','3042'),('32','3047'),('31','3062')])
    assert any(r['bank']=='31' and r['pc']=='3733' for r in native),'ROOTPSRS failure exit not executed'
    assert summary['p63_native_count']==16 and summary['p63_interpretive_pair_fetches']==22 and summary['guidance_interpretive_pair_fetches']==35
    assert any(e['P']=='63' for e in dsky(p/'io.csv'))
    last=dsky(p/'io.csv')[-1];assert (last['V'],last['N'],last['R1'])==('05','09','01406')
    cold=ROOT/'results/cold';assert not rows(cold/'fixture-writes.csv')
    assert not any(r['bank']=='32' for r in rows(cold/'interpretive.csv'))
    assert 'p63_instructions=2' in (cold/'run.txt').read_text()
    assert (p/'io.csv').read_bytes()==(ROOT/'results/uninstrumented/io.csv').read_bytes()
    writes=rows(p/'fixture-writes.csv');assert writes and all(int(r['cycle'])==682666 and 0<=int(r['value'],8)<=0o77777 for r in writes)
    movie=ROOT/'demo/hamilton.mp4'
    assert movie.exists(),'Render the movie before full verification'
    if movie.exists():
        meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
        assert (meta['streams'][0]['width'],meta['streams'][0]['height'])==(1920,1080)
        assert abs(float(meta['format']['duration'])-1210/24)<.1
    print('PASS: reference rope, P63 and guidance execution, real 01406 display, cold-start control, passive tracing, fixture audit, 1080p movie')
if __name__=='__main__':main()
