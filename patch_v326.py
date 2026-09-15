from pathlib import Path
p=Path('index.html')
s=p.read_text()
s=s.replace('Ver.3.25','Ver.3.26')
# Add tsunami safety state to sim initialization near cargoPriority
needle='cargoPriority:{completed:false,revision:0,completedRevision:-1}'
if needle in s:
 s=s.replace(needle,needle+',tsunamiSafety:{active:false,evacuated:false,entryRestricted:false,revision:0}',1)
# Detect tsunami warning event text centrally in event message path; activate mandatory safety response.
needle='function addMessage(side,type,title,text)'
insert='''function tsunamiWarningActive(){return sim.scenario==="EQTS"&&!!sim.tsunamiSafety?.active}\nfunction activateTsunamiSafety(){\n if(!sim.tsunamiSafety)sim.tsunamiSafety={active:false,evacuated:false,entryRestricted:false,revision:0};\n sim.tsunamiSafety.active=true;sim.tsunamiSafety.revision++;\n upsertPendingCritical({kind:"TSUNAMI_EVAC",createdTurn:sim.currentTurn,label:"港湾関係者・現場作業員を安全な場所へ一時避難させ、港内への立入りを制限する"});\n}\nfunction resolveTsunamiEvacuation(){\n sim.tsunamiSafety.evacuated=true;sim.tsunamiSafety.entryRestricted=true;\n sim.pendingCritical=(sim.pendingCritical||[]).filter(x=>x.kind!=="TSUNAMI_EVAC");\n return "人命安全を優先し、港湾関係者・現場作業員の一時避難と港内への立入制限を継続します。津波警報・港内水位変動が収束し、安全が確認されるまで現地立入りを伴う施設確認は実施しません。";\n}\n'''
if needle in s and 'function activateTsunamiSafety()' not in s:
 s=s.replace(needle,insert+needle,1)
# Hook exact event phrase wherever it is emitted: before maybeEvent returns/render paths by wrapping addMessage event calls.
old='addMessage("left","event",'
# Instead add detection inside addMessage using title/text, robust for event source.
fn='function addMessage(side,type,title,text){'
if fn in s:
 s=s.replace(fn,fn+'\n if(type==="event"&&sim?.scenario==="EQTS"&&/津波警報/.test(String(text||""))&&/水位変動/.test(String(text||"")))activateTsunamiSafety();',1)
# Add mandatory option in criticalFollowUps after function opening.
fn='function criticalFollowUps(){'
if fn in s:
 s=s.replace(fn,fn+'\n if(tsunamiWarningActive()&&!sim.tsunamiSafety.evacuated){const e=opt("DEC01","FOLLOW_UP","港湾関係者・現場作業員を安全な場所へ一時避難させ、港内への立入りを制限する");e.priority=1200;e.mandatory=true;e.followUpKind="TSUNAMI_EVAC";return [e,...criticalFollowUpsBase()]}',1)
 # avoid recursion by rename original remainder helper: this transformation needs restructure
 s=s.replace(fn+'\n if(tsunamiWarningActive()&&!sim.tsunamiSafety.evacuated){const e=opt("DEC01","FOLLOW_UP","港湾関係者・現場作業員を安全な場所へ一時避難させ、港内への立入りを制限する");e.priority=1200;e.mandatory=true;e.followUpKind="TSUNAMI_EVAC";return [e,...criticalFollowUpsBase()]}', 'function criticalFollowUpsBase(){',1)
 # insert wrapper before next function after base using known function boundary
 marker='function requiredChoiceRank('
 if marker in s:
  wrapper='function criticalFollowUps(){const a=criticalFollowUpsBase();if(tsunamiWarningActive()&&!sim.tsunamiSafety.evacuated){const e=opt("DEC01","FOLLOW_UP","港湾関係者・現場作業員を安全な場所へ一時避難させ、港内への立入りを制限する");e.priority=1200;e.mandatory=true;e.followUpKind="TSUNAMI_EVAC";return [e,...a]}return a}\n'
  s=s.replace(marker,wrapper+marker,1)
# Handle direct selection before generic follow-up processing.
needle='function handleDecision(option)'
# actual may include brace spacing; use exact likely
for fn in ['function handleDecision(option){','function handleDecision(option) {']:
 if fn in s:
  s=s.replace(fn,fn+'\n if(option?.followUpKind==="TSUNAMI_EVAC"){const t=resolveTsunamiEvacuation();addMessage("left","result","一時避難・立入制限",t);recordHistory(option,"TSUNAMI_EVAC");advanceTurn();return}',1);break
# Batch resolver
needle='if(item.followUpKind==="CARGO_FUNCTION_PRIORITY")'
if needle in s:
 s=s.replace(needle,'if(item.followUpKind==="TSUNAMI_EVAC"){resolveTsunamiEvacuation();lines.push(item.label+"：実施済み")}else '+needle,1)
# Safety filter: while active and not evacuated, only mandatory evacuation plus non-field remote/info choices.
needle='function renderOptions(options)'
for fn in ['function renderOptions(options){','function renderOptions(options) {']:
 if fn in s:
  s=s.replace(fn,fn+'\n if(tsunamiWarningActive()&&!sim.tsunamiSafety.evacuated){const ev=(options||[]).find(x=>x.followUpKind==="TSUNAMI_EVAC")||criticalFollowUps().find(x=>x.followUpKind==="TSUNAMI_EVAC");const safe=(options||[]).filter(x=>x!==ev&&(/情報|監視|船舶|避難|立入|警報/.test(x.label||""))).slice(0,3);options=[ev,...safe].filter(Boolean)}',1);break
# Ensure version changed
assert 'Ver.3.26' in s
assert 'activateTsunamiSafety' in s
assert 'TSUNAMI_EVAC' in s
p.write_text(s)
