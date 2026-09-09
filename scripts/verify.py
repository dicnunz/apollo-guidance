"""Check actual assembly, execution, isolation controls, DSKY decoding and video."""
from pathlib import Path
import csv,json,hashlib,subprocess,tempfile
from decode import dsky,listing
ROOT=Path(__file__).resolve().parents[1]
def rows(p):return list(csv.DictReader(p.open()))
def check_decoder():
    # Upstream yaDSKY2: plus has priority while both relay bits are set.
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'io.csv'
        samples=[(10,0o10,(7<<11)|0o2000),(20,0o10,(6<<11)|0o2000),
                 (30,0o10,7<<11),(40,0o10,6<<11)]
        path.write_text('cycle,channel,value\n'+''.join(f'{t},{c:o},{v:o}\n' for t,c,v in samples))
        events=dsky(path)
        assert [e['signs']['R1'] for e in events]==[' ','+','+','-',' ']
        assert events[0]['cycle']==0 and events[0]['lights']=={}
        assert all(e['t']==e['cycle']*12/1024000 for e in events)


def check_fixture(writes):
    assert len(writes)==47
    final={(int(r['bank'],8),int(r['address'],8)):int(r['value'],8) for r in writes}
    expected={(0,0o77)}|{(3,0o333+i) for i in range(18)}
    expected|={(b,a+i) for b,a,n in [(4,0o22,6),(2,0o220,6),(2,0o226,6),(2,0o234,2),(5,0,2)] for i in range(n)}
    assert set(final)==expected and final[0,0o77]&0o10000
    def dp(bank,address,value):
        stored=final[bank,address]*16384+final[bank,address+1]
        assert stored==round(value*2**28), (bank,address,value,stored)
    for i in range(9):dp(3,0o333+2*i,.5 if i in [0,4,8] else 0)
    for i,v in enumerate([1737400,0,0]):dp(4,0o22+2*i,v/2**27)
    for i,v in enumerate([1752400,0,0]):dp(2,0o220+2*i,v/2**27)
    for i,v in enumerate([0,17,0]):dp(2,0o226+2*i,v/2**7)
    dp(2,0o234,800/2**28);dp(5,0,90000/2**28)


def main():
    check_decoder()
    manifest=json.loads((ROOT/'results/build-manifest.json').read_text())
    assert manifest['reference_binary_matches'] and manifest['binary_bytes']==73728
    assert hashlib.sha256((ROOT/'results/Luminary099.bin').read_bytes()).hexdigest()==manifest['files']['Luminary099/MAIN.agc.bin']
    vendor=ROOT/'vendor/virtualagc'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=vendor,text=True).strip()==manifest['source_commit']=='ebd8695d23bde6eb9f26933ddf244b8d18987f21'
    for name,digest in manifest['files'].items():
        assert hashlib.sha256((vendor/name).read_bytes()).hexdigest()==digest, name
    assert (ROOT/'results/Luminary099.bin').read_bytes()==(vendor/'Luminary099/Luminary099.bin').read_bytes()
    engine=(vendor/'yaAGC/agc_engine.c').read_text()
    anchor='  // Now that the index value has been used, get rid of it.'
    expected=engine.replace(anchor,'  extern void HamiltonTrace(agc_t *, int, int, int);\n  HamiltonTrace(State, ProgramCounter, Instruction, sExtraCode);\n\n'+anchor)
    assert (ROOT/'build/agc_engine.c').read_text()==expected, 'Unexpected instrumentation change'
    assert json.loads((ROOT/'results/source-map.json').read_text())==listing()
    p=ROOT/'results/bench';summary=json.loads((p/'summary.json').read_text());native=rows(p/'trace.csv');interp=rows(p/'interpretive.csv')
    snapshots=rows(p/'snapshots.csv');last_snapshot=snapshots[-1]
    assert summary['machine_cycles']==int(last_snapshot['cycle'])==2560000
    assert summary['instruction_count']==int(last_snapshot['instructions'])>1000000
    coverage=rows(p/'coverage.csv')
    assert summary['p63_native_count']==sum(int(r['count']) for r in coverage if r['bank']=='32' and 0o2776<=int(r['pc'],8)<=0o3350)
    assert summary['p63_interpretive_pair_fetches']==sum(r['bank']=='32' and 0o2776<=int(r['pc'],8)<=0o3350 for r in interp)
    assert summary['guidance_interpretive_pair_fetches']==sum(r['bank']=='31' for r in interp)
    assert json.loads((p/'dsky.json').read_text())==dsky(p/'io.csv')
    assert summary['last_dsky']==dsky(p/'io.csv')[-1]
    for key,cycle in summary['native_path_entry_cycles'].items():
        assert cycle==next((r['cycle'] for r in native if f"{r['bank']},{r['pc']}"==key),None)
    cycles=[int(r['cycle']) for r in rows(p/'io.csv')]
    assert cycles==sorted(cycles) and max(cycles)<=2560000
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
    check_fixture(writes)
    assert writes==rows(ROOT/'results/uninstrumented/fixture-writes.csv')
    movie=ROOT/'demo/hamilton.mp4'
    assert movie.exists(),'Render the movie before full verification'
    if movie.exists():
        meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
        assert (meta['streams'][0]['width'],meta['streams'][0]['height'])==(1920,1080)
        assert abs(float(meta['format']['duration'])-1210/24)<.1
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'],check=True)
    print('PASS: reference rope, P63 and guidance execution, real 01406 display, cold-start control, passive tracing, scaled fixture values, decoder sign priority, 1080p movie and full decode')
if __name__=='__main__':main()
