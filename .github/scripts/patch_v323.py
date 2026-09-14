from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,name):
    global s
    if old not in s:
        raise SystemExit(f'missing target: {name}')
    s=s.replace(old,new,1)

s=s.replace('Ver.3.22','Ver.3.23')

rep(
'majorMistakes:[],utilizationConditions:{},choiceReview:null,offeredOpportunities:new Set(),berthRequired:{altBerth:false,altSurvey:false,resource:false},completedFollowUps:new Set(),completedRelations:new Set(),finished:false,currentOptions:[],warning60:false,overtime:false};',
'majorMistakes:[],utilizationConditions:{},cargoPriority:{completed:false,revision:0,completedRevision:-1},choiceReview:null,offeredOpportunities:new Set(),berthRequired:{altBerth:false,altSurvey:false,resource:false},completedFollowUps:new Set(),completedRelations:new Set(),finished:false,currentOptions:[],warning60:false,overtime:false};',
'sim cargoPriority state')

rep(
'sim.majorMistakes=[];sim.utilizationConditions={};sim.choiceReview=null;sim.offeredOpportunities=new Set();sim.berthRequired={altBerth:false,altSurvey:false,resource:false};',
'sim.majorMistakes=[];sim.utilizationConditions={};sim.cargoPriority={completed:false,revision:0,completedRevision:-1};sim.choiceReview=null;sim.offeredOpportunities=new Set();sim.berthRequired={altBerth:false,altSurvey:false,resource:false};',
'beginScenario cargoPriority reset')

rep(
'function removeUtilizationCondition(dec){removePendingCritical(utilizationConditionKey(dec))}\nfunction resolveUtilizationCondition(dec){',
'''function removeUtilizationCondition(dec){removePendingCritical(utilizationConditionKey(dec))}
function cargoPriorityNeedsAction(){
 const p=sim.cargoPriority;
 return !p?.completed||p.completedRevision<p.revision
}
function requestCargoPriority(){
 if(!cargoPriorityNeedsAction())return;
 upsertPendingCritical({kind:"CARGO_FUNCTION_PRIORITY",createdTurn:sim.currentTurn,label:"重要貨物・主要機能の優先順位を設定する"})
}
function invalidateCargoPriority(){
 if(!sim.cargoPriority)sim.cargoPriority={completed:false,revision:0,completedRevision:-1};
 sim.cargoPriority.revision++;
 requestCargoPriority()
}
function resolveCargoPriority(){
 if(!sim.cargoPriority)sim.cargoPriority={completed:false,revision:0,completedRevision:-1};
 sim.cargoPriority.completed=true;sim.cargoPriority.completedRevision=sim.cargoPriority.revision;
 removePendingCritical("CARGO_FUNCTION_PRIORITY");
 const cargo=sim.scenario==="EQTS"
  ?"緊急支援物資・生活必需品を最優先とし、重要サプライチェーン貨物、一般貨物の順に整理します。"
  :"人命・生活維持に関わる貨物とサプライチェーン影響の大きい重要貨物を優先し、一般貨物は後順位とします。";
 const funcs=sim.scenario==="TCSS"
  ?"主要機能は、安全な入港条件、使用可能岸壁・港内動線、電力・荷役、背後交通の順に復旧・運用条件を整理します。"
  :sim.scenario==="TCHW"
  ?"主要機能は、航行・係留の安全条件、使用可能岸壁、荷役・電力、背後交通の順に再開条件を整理します。"
  :"主要機能は、航路・泊地の安全確保、使用可能岸壁、荷役・電力、背後交通の順に復旧・運用条件を整理します。";
 return `重要貨物と主要機能の優先順位を設定しました。\\n${cargo}\\n${funcs}\\n関係者間で共有し、以後の復旧・代替判断に反映します。`
}
function resolveUtilizationCondition(dec){''',
'cargo priority functions')

rep(
'  if(p.kind?.startsWith("UTIL_CONDITION:")){',
'''  if(p.kind==="CARGO_FUNCTION_PRIORITY"&&cargoPriorityNeedsAction()){
   const x=opt("DEC12","FOLLOW_UP",p.label||"重要貨物・主要機能の優先順位を設定する");
   x.priority=985;x.mandatory=true;x.followUpKind="CARGO_FUNCTION_PRIORITY";o.push(x)
  }
  if(p.kind?.startsWith("UTIL_CONDITION:")){''',
'critical followup cargo priority')

rep(
' if(e.id==="EQ-RELIEF"){\n  msg="被災地域から食料・飲料水等の緊急輸送要請が入りました。";\n  invalidateDecisionPaths("DEC12");invalidateDecisionPaths("DEC13");sim.eventBoosts.DEC12=30;sim.eventBoosts.DEC13=25\n }',
' if(e.id==="EQ-RELIEF"){\n  msg="被災地域から食料・飲料水等の緊急輸送要請が入りました。";\n  invalidateDecisionPaths("DEC12");invalidateCargoPriority();invalidateDecisionPaths("DEC13");sim.eventBoosts.DEC12=30;sim.eventBoosts.DEC13=25\n }',
'relief invalidates priority')

rep(
' if(option.dec==="DEC12"&&atLeast(reported,"L2"))text+="\\n重要貨物・主要機能の優先順位付けが必要です。";',
''' if(option.dec==="DEC12"&&atLeast(reported,"L2")){
  requestCargoPriority();
  text+="\\n重要貨物・主要機能の優先順位付けが必要です。";
  text+=sim.currentTurn<checkEndTurn()?" 次TURN以降、重要対応として選択できます。":" 次の復旧・代替方針で優先順位を設定してください。"
 }''',
'DEC12 request priority')

rep(
' if(sc==="EQTS"&&sim.events.some(x=>x.id==="EQ-RELIEF"))c.push({id:"REC-RELIEF",type:"RECOVERY",dec:"DEC12",label:"緊急物資輸送を優先する"});',
''' if(hasPendingCritical("CARGO_FUNCTION_PRIORITY")&&cargoPriorityNeedsAction())c.unshift({id:"REC-PRIORITY",type:"RECOVERY",dec:"DEC12",label:"重要貨物・主要機能の優先順位を設定する"});
 if(sc==="EQTS"&&sim.events.some(x=>x.id==="EQ-RELIEF")&&!hasPendingCritical("CARGO_FUNCTION_PRIORITY"))c.push({id:"REC-RELIEF",type:"RECOVERY",dec:"DEC12",label:"緊急物資輸送を優先する"});''',
'recovery priority choice')

rep(
'function resolveRecovery(option){\n const appropriateness=recoveryAppropriateness(option);',
'''function resolveRecovery(option){
 const appropriateness=recoveryAppropriateness(option);
 if(option.id==="REC-PRIORITY"){
  const result=resolveCargoPriority();
  sim.recovery={optionId:option.id,label:option.label,successClass:"PRIORITY",outcome:"GOOD",affected:["DEC12"],appropriateness:10};
  return result
 }''',
'resolve recovery priority')

rep(
' if(option.id==="REC-RELIEF"&&sim.scenario==="EQTS"&&sim.events.some(x=>x.id==="EQ-RELIEF"))return 10;',
' if(option.id==="REC-PRIORITY")return 10;\n if(option.id==="REC-RELIEF"&&sim.scenario==="EQTS"&&sim.events.some(x=>x.id==="EQ-RELIEF"))return 10;',
'priority appropriateness')

rep(
'  }else if(item.followUpKind==="UTIL_CONDITION"){\n   resolveUtilizationCondition(item.utilizationDec||item.dec);lines.push(item.label+"：確認済み")',
'  }else if(item.followUpKind==="CARGO_FUNCTION_PRIORITY"){\n   resolveCargoPriority();lines.push(item.label+"：設定済み")\n  }else if(item.followUpKind==="UTIL_CONDITION"){\n   resolveUtilizationCondition(item.utilizationDec||item.dec);lines.push(item.label+"：確認済み")',
'batch cargo priority')

rep(
'  }else if(option.followUpKind==="UTIL_CONDITION"){\n   const dec=option.utilizationDec||option.dec,t=resolveUtilizationCondition(dec);sim.lastResult=null;',
'''  }else if(option.followUpKind==="CARGO_FUNCTION_PRIORITY"){
   const t=resolveCargoPriority();sim.lastResult=null;
   addMessage("left","result","優先順位設定",t,"優先順位設定済み");
   sim.history.push({turn:sim.currentTurn,dec:"DEC12",label:option.label,special:"CARGO_FUNCTION_PRIORITY"})
  }else if(option.followUpKind==="UTIL_CONDITION"){
   const dec=option.utilizationDec||option.dec,t=resolveUtilizationCondition(dec);sim.lastResult=null;''',
'handle cargo priority')

rep(
' if(id==="REC-RELIEF"||label.includes("優先貨物")||label.includes("優先順位")&&label.includes("貨物")||label.includes("重要貨物")&&label.includes("優先"))keys.push("SUPPLY");',
' if(id==="REC-RELIEF"||kind==="CARGO_FUNCTION_PRIORITY"||id==="REC-PRIORITY"||label.includes("優先貨物")||label.includes("優先順位")&&(label.includes("貨物")||label.includes("主要機能"))||label.includes("重要貨物")&&label.includes("優先"))keys.push("SUPPLY");',
'opportunity supply classifier')

rep(
'function registerOfferedOptions(options){\n if(!sim.offeredOpportunities)sim.offeredOpportunities=new Set();\n for(const x of options||[])for(const k of opportunityKeysForOption(x))sim.offeredOpportunities.add(k)\n}',
'''function registerOfferedOptions(options){
 if(!sim.offeredOpportunities)sim.offeredOpportunities=new Set();
 for(const x of options||[]){
  for(const k of opportunityKeysForOption(x))sim.offeredOpportunities.add(k);
  if(x?.type==="REQUIRED_BATCH")for(const item of x.batchItems||[])for(const k of opportunityKeysForOption(item))sim.offeredOpportunities.add(k)
 }
}''',
'batch opportunity registration')

rep(
' if(key==="SUPPLY")return sim.recovery?.optionId==="REC-RELIEF"||hist(x=>/優先貨物|優先順位/.test(x.label||""));',
' if(key==="SUPPLY")return!!sim.cargoPriority?.completed||sim.recovery?.optionId==="REC-RELIEF"||hist(x=>/優先貨物|優先順位/.test(x.label||""));',
'core score supply state')

rep(
'  const cargoPriority=historyHas(x=>x.dec==="ALT"&&x.label?.includes("優先貨物"))||recoveryId==="REC-RELIEF";',
'  const cargoPriority=!!sim.cargoPriority?.completed||historyHas(x=>x.dec==="ALT"&&x.label?.includes("優先貨物"))||recoveryId==="REC-RELIEF"||recoveryId==="REC-PRIORITY";',
'gap supply state')

rep(
'  if(hasPendingCritical("BERTH_RECOVERY_ALT")||hasPendingCritical("ALT_BERTH_CHECK")){',
'''  if(hasPendingCritical("CARGO_FUNCTION_PRIORITY")&&cargoPriorityNeedsAction()){
   addMessage("left","event danger","未確認重要項目","重要貨物・主要機能の優先順位が未設定です。復旧・代替方針の選択肢に優先順位設定を提示します。");
  }
  if(hasPendingCritical("BERTH_RECOVERY_ALT")||hasPendingCritical("ALT_BERTH_CHECK")){''',
'recovery unresolved priority notice')

p.write_text(s,encoding='utf-8')
print('patched Ver.3.23')
