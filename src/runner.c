/* Original Hamilton test harness. MIT licensed; linked yaAGC remains GPL-2.0-or-later. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
#include "yaAGC.h"
#include "agc_engine.h"
static agc_t state;
static FILE *io,*trace,*snap,*interp,*fixture;
static unsigned long long instructions=0,p63hits=0;
static unsigned hits[044][02000];
FILE *rfopen(const char *name,const char *mode){return fopen(name,mode);}
void UnblockSocket(int fd){}
void BacktraceAdd(agc_t *s,int cause){}
void ShiftToDeda(agc_t *s,int data){}
void RequestRadarData(agc_t *s){}
void ChannelRoutine(agc_t *s){}
void ChannelOutput(agc_t *s,int channel,int value){
 if(channel==7){s->InputChannel[7]=s->OutputChannel7=value&0160;return;}
 if(channel==010||channel==011||channel==013||channel==0163)
 fprintf(io,"%llu,%o,%05o\n",(unsigned long long)s->CycleCounter,channel,value&077777);
}
int ChannelInput(agc_t *s){return 0;}
void HamiltonTrace(agc_t *s,int pc,int instruction,int extra){
 int bank=pc>=04000?pc/02000:((s->Erasable[0][RegFB]>>10)&037);
 if(pc>=02000&&pc<04000&&bank>=030&&(s->OutputChannel7&0100))bank+=010;
 instructions++;
 if(pc==06070){int loc=s->Erasable[0][0164]&07777;int ib=(s->Erasable[0][0165]>>10)&037;if(ib>=030&&(s->OutputChannel7&0100))ib+=010;fprintf(interp,"%llu,%02o,%04o\n",(unsigned long long)s->CycleCounter,ib,loc);}
 if(pc>=02000&&bank<044){hits[bank][pc%02000]++;if(bank==032&&pc>=02776&&pc<=03350)p63hits++;}
 if(instructions%1000==0 || (bank==032&&pc>=02776&&pc<=03350) || (bank==031))
 fprintf(trace,"%llu,%llu,%02o,%04o,%05o,%d,%06o,%06o,%04o\n",(unsigned long long)s->CycleCounter,instructions,bank,pc,instruction,extra,s->Erasable[0][RegA]&0177777,s->Erasable[0][RegL]&0177777,s->Erasable[0][RegQ]&07777);
}
static void word(int bank,int address,int value){state.Erasable[bank][address]=value;fprintf(fixture,"%llu,%o,%03o,%05o\n",(unsigned long long)state.CycleCounter,bank,address,value);}
static void dp(int bank,int address,double value){
 int sign=value<0;double x=fabs(value)*16384;int hi=(int)x;int lo=(int)llround((x-hi)*16384);if(lo==16384){hi++;lo=0;}word(bank,address,sign?(hi^077777):hi);word(bank,address+1,sign?(lo^077777):lo);
}
int main(int argc,char **argv){
 if(argc<3||argc>4){fprintf(stderr,"usage: runner rope.bin output_directory [--cold]\n");return 2;}
 int cold=argc==4 && strcmp(argv[3],"--cold")==0;
 char path[2048];snprintf(path,sizeof(path),"%s/io.csv",argv[2]);io=fopen(path,"w");snprintf(path,sizeof(path),"%s/trace.csv",argv[2]);trace=fopen(path,"w");snprintf(path,sizeof(path),"%s/snapshots.csv",argv[2]);snap=fopen(path,"w");if(!io||!trace||!snap)return 3;
 snprintf(path,sizeof(path),"%s/interpretive.csv",argv[2]);interp=fopen(path,"w");fprintf(interp,"cycle,bank,pc\n");
 snprintf(path,sizeof(path),"%s/fixture-writes.csv",argv[2]);fixture=fopen(path,"w");fprintf(fixture,"cycle,bank,address,value\n");
 fprintf(io,"cycle,channel,value\n");fprintf(trace,"cycle,instruction_count,bank,pc,word,extended,a,l,q\n");fprintf(snap,"cycle,instructions,p63_instructions\n");
 if(agc_engine_init(&state,argv[1],NULL,0))return 4;
 ShowAlarms=1;
 // Actual DSKY key codes, injected as KEYRUPT through input channel 015.
 int keys[]={17,3,6,28,17,3,7,28,6,3,28,17,16,5,31,16,9,28};
 double times[]={3,3.4,3.8,4.2,8,8.4,8.8,9.2,9.6,10,10.4,15,15.4,15.8,16.2,16.6,17,17.4};int next=0;
 unsigned long long end=(unsigned long long)(30.0*1024000/12);
 while(state.CycleCounter<end){
  if(next<18 && state.CycleCounter>=(unsigned long long)(times[next]*1024000/12)){
   if(next==4 && !cold){
    word(0,0077,state.Erasable[0][0077]|010000);
    for(int k=0;k<18;k++)word(3,0333+k,0);
    dp(3,0333,0.5);dp(3,0333+8,0.5);dp(3,0333+16,0.5);
    dp(4,0022,1737400.0/pow(2,27));dp(4,0024,0);dp(4,0026,0);
    dp(2,0220,1752400.0/pow(2,27));dp(2,0222,0);dp(2,0224,0);
    dp(2,0226,0);dp(2,0230,17.0/pow(2,7));dp(2,0232,0);
    dp(2,0234,800.0/pow(2,28));dp(5,0,90000.0/pow(2,28));
   }
   state.InputChannel[015]=keys[next];state.InterruptRequests[5]=1;
   fprintf(io,"%llu,15,%05o\n",(unsigned long long)state.CycleCounter,keys[next]);next++;
  }
  agc_engine(&state);
  if(state.CycleCounter%4267==0)fprintf(snap,"%llu,%llu,%llu\n",(unsigned long long)state.CycleCounter,instructions,p63hits);
 }
 fprintf(snap,"%llu,%llu,%llu\n",(unsigned long long)state.CycleCounter,instructions,p63hits);
 fclose(io);fclose(trace);fclose(snap);fclose(interp);fclose(fixture);
 snprintf(path,sizeof(path),"%s/coverage.csv",argv[2]);FILE *c=fopen(path,"w");fprintf(c,"bank,pc,count\n");for(int b=0;b<044;b++)for(int a=0;a<02000;a++)if(hits[b][a])fprintf(c,"%02o,%04o,%u\n",b,(b==2||b==3)?b*02000+a:02000+a,hits[b][a]);fclose(c);
 printf("instructions=%llu p63_instructions=%llu cycles=%llu\n",instructions,p63hits,(unsigned long long)state.CycleCounter);return 0;
}
