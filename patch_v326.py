from pathlib import Path
import re
p=Path('index.html'); s=p.read_text(); s=s.replace('Ver.3.25','Ver.3.26')
m=re.search(r'cargoPriority:\{completed:false,revision:0,completedRevision:-1\}',s)
if m and 'tsunamiSafety:' not in s:s=s[:m.end()]+',tsunamiSafety:{active:false,evacuated:false,entryRestricted:false,revision:0}'+s[m.end():]
helpers='''function tsunamiWarningActive(){return sim.scenario==="EQTS"&&!!sim.tsunamiSafety?.active}\nfunction activateTsunamiSafety(){if(!sim.tsunamiSafety)sim.tsunamiSafety={active:false,evacuated:false,entryRestricted:false,revision:0};sim.tsunamiSafety.active=true;sim.tsunamiSafety.revision++;upsertPendingCritical({kind:"TSUNAMI_EVAC",createdTurn:sim.currentTurn,label:"港湾関係者・現場作業員を安全な場所へ一時避難させ、港内への立入りを制限する"})}\nfunction resolveTsunamiEvacuation(){if(!sim.tsunamiSafety)sim.tsunamiSafety={active:true,evacuated:false,entryRestricted:false,revision:0};sim.tsunamiSafety.evacuated=true;sim.tsunamiSafety.entryRestricted=true;sim.pendingCritical=(sim.pendingCritical||[]).filter(x=>x.kind!=="TSUNAMI_EVAC");return "人命安全を優先し、港湾関係者・現場作業員の一時避難と港内への立入制限を継続します。津波警報・港内水位変動が収束し、安全が確認されるまで現地立入りを伴う施設確認は実施しません。"}\n'''
if 'function activateTsunamiSafety()' not in s:
 m=re.search(r'function\s+(addMessage|addMsg)\s*\([^)]*\)\s*\{',s);assert m,'message function not found';s=s[:m.start()]+helpers+s[m.start():]
m=re.search(r'function\s+(addMessage|addMsg)\s*\(([^)]*)\)\s*\{',s);assert m
params=[x.strip().split('=')[0].strip() for x in m.group(2).split(',')];ptype='type' if 'type' in params else ('kind' if 'kind' in params else params[1]);ptext='text' if 'text' in params else ('body' if 'body' in params else params[-1])
if '&&/水位変動/.test' not in s:s=s[:m.end()]+f'\n if({ptype}==="event"&&sim?.scenario==="EQTS"&&/津波警報/.test(String({ptext}||""))&&/水位変動/.test(String({ptext}||"")))activateTsunamiSafety();'+s[m.end():]
if 'function criticalFollowUpsBase(' not in s:
 m=re.search(r'function\s+criticalFollowUps\s*\(\s*\)\s*\{',s);assert m,'criticalFollowUps not found';s=s[:m.start()]+'function criticalFollowUpsBase(){'+s[m.end():]
 marker=re.search(r'function\s+requiredChoiceRank\s*\(',s);assert marker
 wrapper='function criticalFollowUps(){const a=criticalFollowUpsBase();if(tsunamiWarningActive()&&!sim.tsunamiSafety?.evacuated){const e=opt("DEC01","FOLLOW_UP","港湾関係者・現場作業員を安全な場所へ一時避難させ、港内への立入りを制限する");e.priority=1200;e.mandatory=true;e.followUpKind="TSUNAMI_EVAC";return [e,...a]}return a}\n';s=s[:marker.start()]+wrapper+s[marker.start():]
if 'option?.followUpKind==="TSUNAMI_EVAC"' not in s:
 m=re.search(r'function\s+handleDecision\s*\(\s*option\s*\)\s*\{',s);assert m,'handleDecision not found';code='\n if(option?.followUpKind==="TSUNAMI_EVAC"){const t=resolveTsunamiEvacuation();addMessage("left","result","一時避難・立入制限",t);recordHistory(option,"TSUNAMI_EVAC");advanceTurn();return}';s=s[:m.end()]+code+s[m.end():]
needle='if(item.followUpKind==="CARGO_FUNCTION_PRIORITY")'
if needle in s and 'item.followUpKind==="TSUNAMI_EVAC"' not in s:s=s.replace(needle,'if(item.followUpKind==="TSUNAMI_EVAC"){resolveTsunamiEvacuation();lines.push(item.label+"：実施済み")}else '+needle,1)
# Find the actual UI choice renderer by scanning functions whose body references choiceList.
if 'const ev=(options||[]).find(x=>x.followUpKind==="TSUNAMI_EVAC")' not in s:
 candidates=[]
 for fm in re.finditer(r'function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{',s):
  args=[a.strip().split('=')[0].strip() for a in fm.group(2).split(',') if a.strip()]
  if not args:continue
  pos=fm.end();depth=1;i=pos
  while i<len(s) and depth:
   if s[i]=='{':depth+=1
   elif s[i]=='}':depth-=1
   i+=1
  body=s[pos:i]
  if ('choiceList' in body or 'choice-button' in body) and len(args)>=1:candidates.append((fm,args[0]))
 assert candidates,'choice renderer not found'
 fm,arg=candidates[0]
 code=f'\n if(tsunamiWarningActive()&&!sim.tsunamiSafety?.evacuated){{const ev=({arg}||[]).find(x=>x.followUpKind==="TSUNAMI_EVAC")||criticalFollowUps().find(x=>x.followUpKind==="TSUNAMI_EVAC");const safe=({arg}||[]).filter(x=>x!==ev&&(/情報|監視|船舶|避難|立入|警報/.test(x.label||""))).slice(0,3);{arg}=[ev,...safe].filter(Boolean)}}'
 s=s[:fm.end()]+code+s[fm.end():]
assert 'Ver.3.26' in s and 'activateTsunamiSafety' in s and 'TSUNAMI_EVAC' in s
p.write_text(s)
# retrigger renderer-aware patch
