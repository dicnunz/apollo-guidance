"""Recorded P63 dispatches and DSKY outputs. See docs/design.md."""
from pathlib import Path
from functools import lru_cache
import bisect
import csv
import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'demo'
SOURCE = json.loads((ROOT / 'results/source-map.json').read_text())
DSKY = json.loads((ROOT / 'results/bench/dsky.json').read_text())
DT = [e['t'] for e in DSKY]
EVENTS = []
for kind, name in [('NATIVE', 'trace.csv'), ('INTERPRETIVE', 'interpretive.csv')]:
    for row in csv.DictReader((ROOT / 'results/bench' / name).open()):
        key = f"{row['bank']},{row['pc']}"
        if key in SOURCE and row['bank'] in ('31', '32'):
            EVENTS.append(dict(t=int(row['cycle']) * 12 / 1024000, kind=kind, **SOURCE[key]))
EVENTS.sort(key=lambda e: e['t'])
ET = [e['t'] for e in EVENTS]
BG, INK, GRAY = '#f4f3ee', '#161914', '#42463d'
GREEN, DARK = '#b5dcb7', '#18271f'
FONT_PATHS = [os.environ.get('HAMILTON_FONT', ''), '/System/Library/Fonts/Supplemental/Courier New Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf']
FONT = next((p for p in FONT_PATHS if p and Path(p).exists()), None)
if FONT is None:
    raise RuntimeError('Set HAMILTON_FONT to a monospaced TrueType font.')

@lru_cache(None)
def font(size):
    return ImageFont.truetype(FONT, size)

def text(d, xy, value, size=24, color=INK):
    d.text(xy, str(value), font=font(size), fill=color)

def centered(d, box, value, size=22, color=INK):
    x0, y0, x1, y1 = box
    lines = value.split('\n')
    for j, line in enumerate(lines):
        y = (y0+y1)/2 + (j-(len(lines)-1)/2)*(size+3)
        d.text(((x0+x1)/2, y), line, font=font(size), anchor='mm', fill=color)

SEG = {'0':'abcdef','1':'bc','2':'abdeg','3':'abcdg','4':'bcfg','5':'acdfg','6':'acdefg','7':'abc','8':'abcdefg','9':'abcdfg','-':'g',' ':''}
def digit(d, x, y, char, w=45, h=70):
    t=5
    segments={'a':(x+t,y,x+w-t,y+t),'b':(x+w-t,y+t,x+w,y+h//2-t),'c':(x+w-t,y+h//2+t,x+w,y+h-t),'d':(x+t,y+h-t,x+w-t,y+h),'e':(x,y+h//2+t,x+t,y+h-t),'f':(x,y+t,x+t,y+h//2-t),'g':(x+t,y+h//2-t//2,x+w-t,y+h//2+t//2)}
    for k, box in segments.items():
        if k in SEG.get(char,''):
            d.rectangle(box, fill=GREEN)

def number(d, x, y, value, w=45, h=70):
    for i, char in enumerate(value):
        digit(d,x+i*(w+14),y,char,w,h)

def panel(d, t):
    e = DSKY[max(0, bisect.bisect_right(DT,t)-1)]
    d.rectangle((1150,221,1850,849),fill='#979b92',outline='#64685f',width=2)
    d.rectangle((1168,239,1463,831),fill='#313830')
    d.rectangle((1481,239,1832,831),fill=DARK)
    # Apollo LM LM.ini: two columns of seven annunciators.
    lamps=[('UPLINK\nACTY','9',4),('NO ATT','relay',8),('STBY','115',256),('KEY REL','115',16),('OPR ERR','115',64),('','relay',1),('','relay',2),('TEMP','115',8),('GIMBAL\nLOCK','relay',32),('PROG','relay',256),('RESTART','115',128),('TRACKER','relay',128),('ALT','relay',16),('VEL','relay',4)]
    for n,(label,ch,mask) in enumerate(lamps):
        x=1180+(n//7)*140; y=252+(n%7)*80
        on=bool((e['relay12'] if ch=='relay' else e['lights'].get(ch,0))&mask) and bool(label)
        box=(x,y,x+130,y+68)
        d.rectangle(box,fill=('#e7d987' if n>=7 else '#e7e7db') if on else '#53594e')
        centered(d,box,label,21,'#171a14' if on else '#c1c7b7')
    centered(d,(1500,255,1635,335),'COMP\nACTY',22,GREEN if e['lights'].get('9',0)&2 else '#718675')
    centered(d,(1680,253,1810,289),'PROG',24,GREEN)
    number(d,1690,301,e['P'])
    for x,label,key in [(1500,'VERB','V'),(1690,'NOUN','N')]:
        blank=bool(e['lights'].get('115',0)&0o40)
        if not blank:
            text(d,(x,399),label,24,GREEN)
            number(d,x,439,e[key])
    for j,key in enumerate(('R1','R2','R3')):
        y=555+j*87
        text(d,(1493,y+12),e['signs'][key],35,GREEN)
        number(d,1530,y,e[key],43,65)
        if j<2: d.line((1498,y+77,1813,y+77),fill='#69846c',width=2)

def frame(t, slow=False, hold=False):
    im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
    text(d,(65,58),'LUMINARY 099',30)
    text(d,(65,104),'P63: THE LUNAR LANDING, BRAKING PHASE',24)
    text(d,(1470,65),f'{t:07.3f} s',27)
    text(d,(1470,108),'HOLD' if hold else '0.04x' if slow else '1x',24,GRAY)
    d.line((65,164,1850,164),fill=INK,width=2)
    idx=bisect.bisect_right(ET,t)-1
    if idx>=0:
        event=EVENTS[idx]
        text(d,(65,214),event['source'].replace('.agc',''),22)
        text(d,(65,260),event['kind']+'   '+event['bank']+','+event['pc'],22,GRAY)
        same=sorted((x for x in SOURCE.values() if x['source']==event['source'] and x['bank']==event['bank']),key=lambda x:int(x['pc'],8))
        at=next((i for i,x in enumerate(same) if x['pc']==event['pc']),0)
        start=max(0,min(at-5,len(same)-12))
        for j,row in enumerate(same[start:start+12]):
            y=337+j*43
            active=row['pc']==event['pc']
            if active:d.rectangle((62,y-4,1080,y+33),fill='#dedfd6')
            text(d,(73,y),row['pc'],25,INK if active else GRAY)
            text(d,(166,y),row['word'],25,GRAY)
            # Listing columns retain instruction and operand spacing.
            text(d,(276,y),row['text'].strip()[:52],25)
    else:
        text(d,(65,224),'KEYBOARD INPUT',23)
        text(d,(65,338),'03.000 s    V36E',25)
        text(d,(65,399),'08.000 s    V37E63E',25)
    panel(d,t)
    d.line((65,918,1850,918),fill='#969b91',width=1)
    text(d,(65,951),'Synthetic initial conditions. No spacecraft dynamics.',24)
    if t>=11.26:
        text(d,(65,999),'01406   ROOTPSRS: bad return',24)
    else:
        text(d,(65,999),'Source: last recorded dispatch',23,GRAY)
    return im

def main():
    OUT.mkdir(exist_ok=True)
    frame(10.85,True).save(OUT/'poster.png')
    frame(10.85,True).save(OUT/'execution.png')
    frame(29.8,hold=True).save(OUT/'result.png')
    proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'hamilton.mp4')],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
    try:
        for n in range(1210):
            at=n/24
            if at<5:t,slow=0,False
            elif at<15.4:t,slow=at-5,False
            elif at<36.4:t,slow=10.4+(at-15.4)*.04,True
            elif at<43.4:t,slow=11.24+(at-36.4),False
            else:t,slow=29.8,False
            proc.stdin.write(frame(t,slow,at<5 or at>=43.4).tobytes())
    finally:
        proc.stdin.close()
    if proc.wait():raise RuntimeError('FFmpeg failed')
    print(OUT/'hamilton.mp4')

if __name__=='__main__':main()
