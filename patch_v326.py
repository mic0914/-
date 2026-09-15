from pathlib import Path
import re
p=Path('index.html')
s=p.read_text()
s=s.replace('Ver.3.25','Ver.3.26')
# state: inject beside cargo priority state when available
m=re.search(r'cargoPriority:\{completed:false,revision:0,completedRevision:-1\}',s)
if m and 'tsunamiSafety:' not in s:
 s=s[:m.end()]+',tsunamiSafety:{active:false,evacuated:false,entryRestricted:false,revision:0}'+s[m.end():]
# safety helpers before message renderer
helpers='''function tsunamiWarningActive(){return sim.scenario==="EQTS"&&!!sim.tsunamiSafety?.active}\nfunction activateTsunamiSafety(){\n if(!sim.tsunamiSafety)sim.tsunamiSafety={active:false,evacuated:false,entryRestricted:false,revision:0};\n sim.tsunamiSafety.active=true;sim.tsunamiSafety.revision++;\n upsertPendingCritical({kind:"TSUNAMI_EVAC",createdTurn:sim.currentTurn,label:"港湾関係者・現場作業員を安全な場所へ一時避難させ、港内への立入りを制限する"});\n}\nfunction resolveTsunamiEvacuation(){\n if(!sim.tsunamiSafety)sim.tsunamiSafety={active:true,evacuated:false,entryRestricted:false,revision:0};\n sim.tsunamiSafety.evacuated=true;sim.tsunamiSafety.entryRestricted=true;\n sim.pendingCritical=(sim.pendingCritical||[]).filter(x=>x.kind!=="TSUNAMI_EVAC");\n return "人命安全を優先し、港湾関係者・現場作業員の一時避難と港内への立入制限を継続します。津波警報・港内水位変動が収束し、安全が確認されるまで現地立入りを伴う施設確認は実施しません。";\n}\n'''
if 'function activateTsunamiSafety()' not in s:
 m=re.search(r'function\s+addMessage\s*\([^)]*\)\s*\{',s)
 if not m: m=re.search(r'function\s+addMsg\s*\([^)]*\)\s*\{',s)
 assert m,'message function not found'
 s=s[:m.start()]+helpers+s[m.start():]
# activate on event text at message function entry
m=re.search(r'function\s+(addMessage|addMsg)\s*\(([^)]*)\)\s*\{',s)
assert m,'message function not found after helper insertion'
params=[x.strip().split('=')[0].strip() for x in m.group(2).split(',')]
# infer likely type/text parameter names
ptype='type' if 'type' in params else ('kind' if 'kind' in params else (params[1] if len(params)>1 else '""'))
ptext='text' if 'text' in params else ('body' if 'body' in params else (params[-1] if params else '""'))
hook=f'\n if({ptype}==="event"&&sim?.scenario==="EQTS"&&/津波警報/.test(String({ptext}||""))&&/水位変動/.test(String({ptext}||"")))activateTsunamiSafety();'
if '&&/水位変動/.test' not in s:
 s=s[:m.end()]+hook+s[m.end():]
# wrap critical followups
if 'function criticalFollowUpsBase(' not in s:
 m=re.search(r'function\s+criticalFollowUps\s*\(\s*\)\s*\{',s)
 assert m,'criticalFollowUps not found'
 s=s[:m.start()]+'function criticalFollowUpsBase(){'+s[m.end():]
 marker=re.search(r'function\s+requiredChoiceRank\s*\(',s)
 assert marker,'requiredChoiceRank not found'
 wrapper='function criticalFollowUps(){const a=criticalFollowUpsBase();if(tsunamiWarningActive()&&!sim.tsunamiSafety?.evacuated){const e=opt("DEC01","FOLLOW_UP","港湾関係者・現場作業員を安全な場所へ一時避難させ、港内への立入りを制限する");e.priority=1200;e.mandatory=true;e.followUpKind="TSUNAMI_EVAC";return [e,...a]}return a}\n'
 s=s[:marker.start()]+wrapper+s[marker.start():]
# direct choice handler
if 'option?.followUpKind==="TSUNAMI_EVAC"' not in s:
 m=re.search(r'function\s+handleDecision\s*\(\s*option\s*\)\s*\{',s)
 assert m,'handleDecision not found'
 code='\n if(option?.followUpKind==="TSUNAMI_EVAC"){const t=resolveTsunamiEvacuation();addMessage("left","result","一時避難・立入制限",t);recordHistory(option,"TSUNAMI_EVAC");advanceTurn();return}'
 s=s[:m.end()]+code+s[m.end():]
# batch resolver when cargo marker exists
needle='if(item.followUpKind==="CARGO_FUNCTION_PRIORITY")'
if needle in s and 'item.followUpKind==="TSUNAMI_EVAC"' not in s:
 s=s.replace(needle,'if(item.followUpKind==="TSUNAMI_EVAC"){resolveTsunamiEvacuation();lines.push(item.label+"：実施済み")}else '+needle,1)
# filter choices until evacuation selected
if 'const ev=(options||[]).find(x=>x.followUpKind==="TSUNAMI_EVAC")' not in s:
 m=re.search(r'function\s+renderOptions\s*\(\s*options\s*\)\s*\{',s)
 assert m,'renderOptions not found'
 code='\n if(tsunamiWarningActive()&&!sim.tsunamiSafety?.evacuated){const ev=(options||[]).find(x=>x.followUpKind==="TSUNAMI_EVAC")||criticalFollowUps().find(x=>x.followUpKind==="TSUNAMI_EVAC");const safe=(options||[]).filter(x=>x!==ev&&(/情報|監視|船舶|避難|立入|警報/.test(x.label||""))).slice(0,3);options=[ev,...safe].filter(Boolean)}'
 s=s[:m.end()]+code+s[m.end():]
assert 'Ver.3.26' in s
assert 'activateTsunamiSafety' in s
assert 'TSUNAMI_EVAC' in s
p.write_text(s)
# retrigger robust patch
