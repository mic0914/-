from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,name,count=1):
    global s
    if old not in s:
        raise SystemExit(f'missing target: {name}')
    s=s.replace(old,new,count)

s=s.replace('Ver.3.23','Ver.3.24')

# Track the first phase in which each semantic response opportunity was actually shown.
rep(
'function registerOfferedOptions(options){\n if(!sim.offeredOpportunities)sim.offeredOpportunities=new Set();\n for(const x of options||[]){\n  for(const k of opportunityKeysForOption(x))sim.offeredOpportunities.add(k);\n  if(x?.type==="REQUIRED_BATCH")for(const item of x.batchItems||[])for(const k of opportunityKeysForOption(item))sim.offeredOpportunities.add(k)\n }\n}',
'''function registerOfferedOptions(options){
 if(!sim.offeredOpportunities)sim.offeredOpportunities=new Set();
 if(!sim.opportunityPhases)sim.opportunityPhases=new Map();
 const registerKey=k=>{
  sim.offeredOpportunities.add(k);
  if(!sim.opportunityPhases.has(k))sim.opportunityPhases.set(k,sim.currentTurn)
 };
 for(const x of options||[]){
  for(const k of opportunityKeysForOption(x))registerKey(k);
  if(x?.type==="REQUIRED_BATCH")for(const item of x.batchItems||[])for(const k of opportunityKeysForOption(item))registerKey(k)
 }
}
function opportunityPhase(key){return sim.opportunityPhases?.get(gapOpportunityKey(key))??null}
function phaseLabel(turn=sim.currentTurn){return `Phase ${turn}`}
function phaseGapText(key,text){const p=opportunityPhase(key);return p?`${phaseLabel(p)}で、${text}`:text}''',
'phase opportunity tracking')

# Reset phase tracking on every new simulation.
rep(
'sim.majorMistakes=[];sim.utilizationConditions={};sim.cargoPriority={completed:false,revision:0,completedRevision:-1};sim.choiceReview=null;sim.offeredOpportunities=new Set();sim.berthRequired={altBerth:false,altSurvey:false,resource:false};',
'sim.majorMistakes=[];sim.utilizationConditions={};sim.cargoPriority={completed:false,revision:0,completedRevision:-1};sim.choiceReview=null;sim.offeredOpportunities=new Set();sim.opportunityPhases=new Map();sim.berthRequired={altBerth:false,altSurvey:false,resource:false};',
'begin scenario phase reset')

# Every selection-result card is now identified by sequential Phase number.
replacements={
'addMessage("left","result","重要確認一括対応",t,"重要確認を一括実施");':'addMessage("left","result",phaseLabel(),t,"重要確認を一括実施");',
'addMessage("left","result","代替港情報",t,"広域港湾BCP");':'addMessage("left","result",phaseLabel(),t,"広域港湾BCP");',
'addMessage("left","result","被害拡大対応",t,"後半一括対応");':'addMessage("left","result",phaseLabel(),t,"後半一括対応");',
'addMessage("left","result","岸壁対応",t,"応急復旧＋代替施設");':'addMessage("left","result",phaseLabel(),t,"応急復旧＋代替施設");',
'addMessage("left","result","代替岸壁情報",t,`代替岸壁：${localAltBerthText(sim.altBerth.actual)}`);':'addMessage("left","result",phaseLabel(),t,`代替岸壁：${localAltBerthText(sim.altBerth.actual)}`);',
'addMessage("left","result","復旧資源確認",`作業船・重機・資材等の復旧資源を確認しました。\\n復旧資源：${sim.actual.DEC10}「${LEVEL_LABEL[sim.actual.DEC10]}」`,"復旧資源確認済み");':'addMessage("left","result",phaseLabel(),`作業船・重機・資材等の復旧資源を確認しました。\\n復旧資源：${sim.actual.DEC10}「${LEVEL_LABEL[sim.actual.DEC10]}」`,"復旧資源確認済み");',
'addMessage("left","result","優先順位設定",t,"優先順位設定済み");':'addMessage("left","result",phaseLabel(),t,"優先順位設定済み");',
'addMessage("left","result","利用条件確認",t,"利用条件確認済み");':'addMessage("left","result",phaseLabel(),t,"利用条件確認済み");',
'addMessage("left","result","浸水対応",t,"高潮・浸水対応");':'addMessage("left","result",phaseLabel(),t,"高潮・浸水対応");',
'addMessage("left","result","調査結果",r.text+`':'addMessage("left","result",phaseLabel(),r.text+`',
'else if(sim.currentTurn===recoveryTurn()){const t=resolveRecovery(option);addMessage("left","result","復旧・代替結果",t);':'else if(sim.currentTurn===recoveryTurn()){const t=resolveRecovery(option);addMessage("left","result",phaseLabel(),t);'
}
for old,new in replacements.items(): rep(old,new,'result phase label: '+old[:35])

# Gap comments now identify the phase where the missed response was actually offered.
rep(
'const add=(priority,key,text)=>{if(!opportunityWasOffered(key))return;if(!c.some(x=>x.key===key))c.push({priority,key,text})};',
'const add=(priority,key,text)=>{if(!opportunityWasOffered(key))return;if(!c.some(x=>x.key===key))c.push({priority,key,text:phaseGapText(key,text)})};',
'gap phase prefix')

rep(
'if(!c.some(x=>x.key==="L2_UTILIZATION"))c.push({priority:83,key:"L2_UTILIZATION",text})',
'if(!c.some(x=>x.key==="L2_UTILIZATION")){const phases=l2Needs.map(name=>{const dec=Object.keys(DEC_META).find(d=>DEC_META[d].name===name);return dec?opportunityPhase("L2_UTILIZATION:"+dec):null}).filter(x=>x!=null);const p=phases.length?Math.min(...phases):null;c.push({priority:83,key:"L2_UTILIZATION",text:p?`${phaseLabel(p)}で、${text}`:text})}',
'L2 gap phase')

rep(
'if(!c.some(x=>x.key==="STALE"))c.push({priority:88,key:"STALE",text})',
'if(!c.some(x=>x.key==="STALE")){const phases=staleCritical.map(([d])=>opportunityPhase("STALE:"+d)).filter(x=>x!=null);const p=phases.length?Math.min(...phases):null;c.push({priority:88,key:"STALE",text:p?`${phaseLabel(p)}で、${text}`:text})}',
'stale gap phase')

# Final result wording clarifies the Phase notation.
rep(
'addMessage("left","score","不足していた対応",gapText+"\\n\\n※ その時点で必要な重要対応は、',
'addMessage("left","score","不足していた対応",gapText+"\\n\\n※ Phase番号は、その対応候補が実際に提示された選択段階を示します。\\n※ その時点で必要な重要対応は、',
'gap note phase meaning')

p.write_text(s,encoding='utf-8')
print('patched Ver.3.24')
