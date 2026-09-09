"""Render source execution beside a relay-decoded DSKY, using captured telemetry only."""
from pathlib import Path
import json,csv,bisect,subprocess
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'demo';OUT.mkdir(exist_ok=True)
BG='#0b1113';PANEL='#162023';FG='#edf1e8';MUTED='#91a099';GREEN='#b9f294';AMBER='#eec17c';LINE='#344139'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';MONO='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def f(n,bold=False,mono=False):return ImageFont.truetype(MONO if mono else BOLD if bold else FONT,n)
def txt(d,xy,s,n=24,fill=FG,bold=False,mono=False):d.text(xy,s,font=f(n,bold,mono),fill=fill)
DSKY=json.loads((ROOT/'results/bench/dsky.json').read_text());DT=[e['t'] for e in DSKY];SOURCE=json.loads((ROOT/'results/source-map.json').read_text());SUMMARY=json.loads((ROOT/'results/bench/summary.json').read_text())
EVENTS=[]
for typ,name in [('NATIVE','trace.csv'),('INTERPRETIVE','interpretive.csv')]:
 for r in csv.DictReader((ROOT/'results/bench'/name).open()):
  key=f"{r['bank']},{r['pc']}"
  if key in SOURCE and (r['bank'] in ['31','32']):EVENTS.append({'t':int(r['cycle'])*12/1024000,'type':typ,**SOURCE[key]})
EVENTS.sort(key=lambda x:x['t']);ET=[e['t'] for e in EVENTS]
SNAPS=list(csv.DictReader((ROOT/'results/bench/snapshots.csv').open()));ST=[int(s['cycle'])*12/1024000 for s in SNAPS]
SEG={'0':'ab cdef'.replace(' ',''),'1':'bc','2':'abdeg','3':'abcdg','4':'bcfg','5':'acdfg','6':'acdefg','7':'abc','8':'abcdefg','9':'abcdfg','-':'g',' ':''}
def digit(d,x,y,char,w=51,h=89):
 t=6;segments={'a':(x+t,y,x+w-t,y+t),'b':(x+w-t,y+t,x+w,y+h//2-t),'c':(x+w-t,y+h//2+t,x+w,y+h-t),'d':(x+t,y+h-t,x+w-t,y+h),'e':(x,y+h//2+t,x+t,y+h-t),'f':(x,y+t,x+t,y+h//2-t),'g':(x+t,y+h//2-t//2,x+w-t,y+h//2+t//2)}
 for k,box in segments.items():d.rounded_rectangle(box,radius=2,fill=GREEN if k in SEG.get(char,'') else '#1c2e25')
def number(d,x,y,s,w=51,h=89,gap=14):
 for i,c in enumerate(s):digit(d,x+i*(w+gap),y,c,w,h)
def base(chapter):
 im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im);txt(d,(66,38),'H A M I L T O N',26,bold=True);txt(d,(1350,42),'APOLLO 11  /  LUMINARY 099',19,MUTED);d.line((65,95,1855,95),fill=LINE,width=2);txt(d,(65,1020),chapter,18,MUTED);return im

def dsky(im,t):
 e=DSKY[max(0,bisect.bisect_right(DT,t)-1)];d=ImageDraw.Draw(im);x,y=1160,226
 d.rounded_rectangle((x,y,1850,948),radius=20,fill='#53605a',outline='#79867d',width=2)
 d.rounded_rectangle((x+24,y+24,1826,730),radius=10,fill='#111c17')
 for xx,label,val in [(x+48,'PROG',e['P']),(x+236,'VERB',e['V']),(x+427,'NOUN',e['N'])]:
  txt(d,(xx,y+46),label,21,GREEN,mono=True)
  if label in ['VERB','NOUN'] and e['lights'].get('115',0)&0o40:val='  '
  number(d,xx,y+87,val,49,84)
 for j,key in enumerate(['R1','R2','R3']):
  yy=y+214+j*94;txt(d,(x+47,yy+24),key,20,MUTED,mono=True);number(d,x+142,yy,e[key],49,76,20)
  sign=e['signs'][key];txt(d,(x+99,yy+12),sign,40,GREEN,mono=True)
 indicators=[('NO ATT',bool(e['relay12']&8)),('PROG',bool(e['relay12']&256)),('RESTART',bool(e['lights'].get('115',0)&128)),('OPR ERR',bool(e['lights'].get('115',0)&64))]
 for j,(label,on) in enumerate(indicators):
  xx=x+28+j*161;d.rounded_rectangle((xx,758,xx+148,803),radius=4,fill=AMBER if on else '#37423c');txt(d,(xx+13,768),label,18,'#161c17' if on else '#84938a',bold=True)
 keys=['VERB','NOUN','+','7','8','9','CLR','−','4','5','6','PRO','0','1','2','3','ENTR','RSET']
 for j,key in enumerate(keys):
  xx=x+28+(j%9)*72;yy=834+(j//9)*48;d.rounded_rectangle((xx,yy,xx+63,yy+37),radius=4,fill='#29352e');txt(d,(xx+6,yy+9),key,13,FG,mono=True)
 return e

def live(t,slow=False):
 im=base('02  /  REAL FLIGHT CODE. REAL OUTPUT CHANNELS.');d=ImageDraw.Draw(im)
 title='Selecting the landing program' if t<10.44 else 'Inside the ignition algorithm' if t<11.25 else 'The program reports its limit'
 txt(d,(65,124),title,51,bold=True);txt(d,(68,191),f'AGC time {t:06.3f} s   /   '+('0.04× playback — instruction trace expanded' if slow else '1× playback'),23,AMBER)
 e=dsky(im,t);d=ImageDraw.Draw(im)
 d.rounded_rectangle((65,262,1095,815),radius=10,fill=PANEL)
 index=bisect.bisect_right(ET,t)-1
 if index>=0:
  event=EVENTS[index];txt(d,(90,284),event['source'].replace('.agc',''),20,MUTED,mono=True)
  txt(d,(90,322),f"{event['type']}  /  BANK {event['bank']}  /  {event['pc']}  /  {event['word']}",19,AMBER,mono=True)
  same=[x for x in SOURCE.values() if x['source']==event['source'] and x['bank']==event['bank']];same.sort(key=lambda x:int(x['pc'],8));where=next((i for i,x in enumerate(same) if x['pc']==event['pc']),0);start=max(0,where-3)
  for j,row in enumerate(same[start:start+9]):
   yy=379+j*40;active=row['pc']==event['pc']
   if active:d.rectangle((80,yy-3,1080,yy+34),fill='#354334')
   txt(d,(94,yy),row['pc'],21,AMBER if active else MUTED,mono=True)
   txt(d,(180,yy),row['text'].strip()[:60],21,FG if active else '#aebbb1',mono=True)
  if event['comment']:txt(d,(92,769),event['comment'][:75],19,MUTED)
 else:
  txt(d,(94,382),'V36E   Fresh start',31,FG,mono=True);txt(d,(94,451),'V37E63E   Request program 63',31,FG,mono=True)
  txt(d,(94,556),'Keystrokes enter channel 015.',24,MUTED);txt(d,(94,599),'The flight program controls every displayed digit.',24,MUTED)
 snap=SNAPS[max(0,bisect.bisect_right(ST,t)-1)];txt(d,(70,848),f"{int(snap['instructions']):,}",52,GREEN,bold=True);txt(d,(73,916),'executed native instructions',22,MUTED)
 txt(d,(637,853),'SYNTHETIC STATE FIXTURE',21,AMBER,bold=True);txt(d,(637,895),'Aligned reference; hypothetical orbit.',20,MUTED);txt(d,(637,931),'No spacecraft dynamics or mission telemetry.',19,MUTED)
 return im

def intro():
 im=base('01  /  ASSEMBLED FROM THE ORIGINAL LISTING');d=ImageDraw.Draw(im)
 txt(d,(70,204),'Run the code',96,bold=True);txt(d,(70,322),'that aimed for the Moon.',76,bold=True)
 txt(d,(75,486),'Luminary 099. The real P63 entry and guidance logic.',30,AMBER)
 for j,s in enumerate(['Original source → yaYUL assembler → yaAGC execution','A DSKY display decoded from the computer’s output','A controlled experiment, including its real failure']):txt(d,(76,590+j*64),s,29,MUTED)
 txt(d,(76,870),'36,864 words',42,GREEN,bold=True);txt(d,(600,880),'Assembly matches the reference rope byte for byte.',26,MUTED)
 return im

def closing():
 im=base('03  /  EVIDENCE, INCLUDING THE FAILURE');d=ImageDraw.Draw(im)
 txt(d,(70,143),'The result is 01406.',66,bold=True);txt(d,(75,240),'The time-to-go root calculation did not return a usable solution.',29,AMBER)
 dsky(im,29.8);d=ImageDraw.Draw(im)
 lines=[(f"{SUMMARY['instruction_count']:,}",'native instructions executed'),(f"{SUMMARY['p63_interpretive_pair_fetches']} + {SUMMARY['guidance_interpretive_pair_fetches']}",'P63 and guidance interpretive pair fetches'),('BYTE-IDENTICAL','DSKY writes with tracing on and off')]
 for j,(value,label) in enumerate(lines):
  yy=349+j*168;txt(d,(75,yy),value,47,GREEN,bold=True);txt(d,(78,yy+69),label,25,MUTED)
 txt(d,(78,880),'P63 executed. A landing was not simulated.',27,FG,bold=True);txt(d,(78,932),'The fixture lacks a complete mission pad load and ephemeris.',22,MUTED)
 return im

def main():
 intro().save(OUT/'poster.png');live(10.85,True).save(OUT/'execution.png');closing().save(OUT/'result.png')
 fps=24;proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'hamilton.mp4')],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
 # 5s title; 10.4s normal; .84s stretched to 21s; 7s normal; 7s results = 50.4s.
 frames=1210
 try:
  for n in range(frames):
   at=n/fps
   if at<5:im=intro()
   elif at<15.4:im=live(at-5)
   elif at<36.4:im=live(10.4+(at-15.4)*.04,True)
   elif at<43.4:im=live(11.24+(at-36.4))
   else:im=closing()
   d=ImageDraw.Draw(im);d.rectangle((65,985,65+1790*(n+1)/frames,988),fill=AMBER)
   proc.stdin.write(im.tobytes())
 finally:proc.stdin.close()
 if proc.wait():raise RuntimeError('FFmpeg failed')
 print(OUT/'hamilton.mp4')
if __name__=='__main__':main()
