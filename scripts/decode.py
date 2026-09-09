"""Decode actual DSKY relay writes and associate executed addresses with listings."""
from pathlib import Path
import csv,json,re
ROOT=Path(__file__).resolve().parents[1]
DIGITS={0:' ',21:'0',3:'1',25:'2',27:'3',15:'4',30:'5',28:'6',19:'7',29:'8',31:'9'}
ROWS={11:[('P',0),('P',1)],10:[('V',0),('V',1)],9:[('N',0),('N',1)],8:[None,('R1',0)],7:[('R1',1),('R1',2)],6:[('R1',3),('R1',4)],5:[('R2',0),('R2',1)],4:[('R2',2),('R2',3)],3:[('R2',4),('R3',0)],2:[('R3',1),('R3',2)],1:[('R3',3),('R3',4)]}

def dsky(path):
    d={k:[' ']*n for k,n in [('P',2),('V',2),('N',2),('R1',5),('R2',5),('R3',5)]};relays={};events=[];lights={};signs={'R1':[0,0],'R2':[0,0],'R3':[0,0]}
    for x in csv.DictReader(path.open()):
        c=int(x['channel'],8);v=int(x['value'],8);cycle=int(x['cycle']);row=v>>11
        if c==0o10:
            relays[row]=v
            if row in ROWS:
                for target,code in zip(ROWS[row],[(v>>5)&31,v&31]):
                    if target:d[target[0]][target[1]]=DIGITS.get(code,'?')
            if row in [7,6,5,4,2,1]:
                r={7:'R1',6:'R1',5:'R2',4:'R2',2:'R3',1:'R3'}[row];i=0 if row in[7,5,2] else 1;signs[r][i]=bool(v&0o2000)
        if c in [0o11,0o163]:lights[str(c)]=v
        if c!=0o15:
            events.append({'cycle':cycle,'t':cycle*12/1024000,**{k:''.join(v) for k,v in d.items()},'signs':{k:'+' if v[0] and not v[1] else '-' if v[1] and not v[0] else ' ' for k,v in signs.items()},'lights':dict(lights),'relay12':relays.get(12,0)})
    return events

def listing():
    source={};file=''
    for line in (ROOT/'vendor/virtualagc/Luminary099/Luminary099.lst').read_text().splitlines():
        if '## Filename:' in line:file=line.split('## Filename:',1)[1].strip()
        m=re.match(r'^\d+,(\d+):\s+(?:(\d\d),)?([0-7]{4})\s+([0-7]{5})\s+',line)
        if m:
            bank=m[2] or f'{int(m[3],8)//1024:02o}';pc=m[3]
            source[f'{bank},{pc}']={'bank':bank,'pc':pc,'word':m[4],'line':int(m[1]),'source':file,'text':line[43:].split('\t#')[0].rstrip(),'comment':line.split('\t#',1)[1].strip() if '\t#' in line else ''}
    return source

def main():
    p=ROOT/'results/bench';events=dsky(p/'io.csv');(p/'dsky.json').write_text(json.dumps(events,separators=(',',':')))
    sources=listing();(ROOT/'results/source-map.json').write_text(json.dumps(sources,separators=(',',':')))
    basic=list(csv.DictReader((p/'trace.csv').open()));interp=list(csv.DictReader((p/'interpretive.csv').open()))
    p63=[r for r in interp if r['bank']=='32' and 0o2776<=int(r['pc'],8)<=0o3350];guidance=[r for r in interp if r['bank']=='31'];cov=list(csv.DictReader((p/'coverage.csv').open()))
    labels={key:next((r['cycle'] for r in basic if f"{r['bank']},{r['pc']}"==key),None) for key in ['32,2776','31,2455','31,3733']}
    out={'duration_seconds':30,'machine_cycles':2560000,'instruction_count':int(list(csv.DictReader((p/'snapshots.csv').open()))[-1]['instructions']),'p63_native_count':sum(int(r['count']) for r in cov if r['bank']=='32' and 0o2776<=int(r['pc'],8)<=0o3350),'p63_interpretive_pair_fetches':len(p63),'guidance_interpretive_pair_fetches':len(guidance),'native_path_entry_cycles':labels,'last_dsky':events[-1],'alarm_01406_displayed':any('01406' in [e['R1'],e['R2'],e['R3']] for e in events),'initialized_fixture':'hypothetical lunar orbit and aligned identity reference; no mission telemetry or spacecraft dynamics'}
    (p/'summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
