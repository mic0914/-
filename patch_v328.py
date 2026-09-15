from pathlib import Path
p=Path('index.html')
s=p.read_text()
s=s.replace('Ver.3.28','Ver.3.29')

# Four response routes are retained as important candidates, but are not forced into the first four choices.
anchor='function criticalFollowUpsBase(){'
helper='''function requestShipAcceptanceResponses(){
 const items=[
  ["SHIP_WAIT","対象船舶の入港を見合わせ、安全な海域で待機させる",965],
  ["SHIP_ALT_BERTH","利用可能な別岸壁と、船型・喫水等の受入条件を確認する",945],
  ["SHIP_ALT_PORT",altPortAlreadyConsidered()?"確認済みの代替港について船会社・荷主と利用調整する":"代替港への寄港変更について船会社・荷主と調整する",935],
  ["SHIP_REENTRY","航路・泊地・岸壁の安全性を再確認し、受入再開条件を整理する",955]
 ];
 for(const [kind,label,priority] of items)if(!hasPendingCritical(kind))upsertPendingCritical({kind,createdTurn:sim.currentTurn,label,priority})
}
function resolveShipAcceptanceResponse(option){
 const kind=option.followUpKind;
 removePendingCritical(kind);
 if(kind==="SHIP_WAIT")return "対象船舶の入港を見合わせ、船会社へ安全な海域での待機を要請しました。港内の安全条件が確認できるまで入港を再開しません。";
 if(kind==="SHIP_ALT_BERTH"){
  sim.altBerth.known=true;
  const v=sim.altBerth.actual;
  return `別岸壁と船舶受入条件を確認しました。\\n・代替岸壁：${localAltBerthText(v)}\\n船型・喫水・係留条件・荷役範囲を踏まえて使用可否を判断します。`
 }
 if(kind==="SHIP_ALT_PORT"){
  activateAlternativePortIfNeeded();
  if(sim.altPorts?.surveyCompleted)return "確認済みの代替港情報を用いて、船会社・荷主との寄港変更・貨物振替の利用調整へ進みます。代替港A・Bの検討を最初からやり直しません。";
  return "船会社・荷主と寄港変更の調整を開始し、代替港の受入可否・荷役余力・背後輸送条件の確認へ進みます。"
 }
 if(kind==="SHIP_REENTRY"){
  for(const d of["DEC03","DEC05","DEC13"])Object.assign(sim.known[d],{level:sim.actual[d],confidence:"A",confirmed:true,lastCheckedTurn:sim.currentTurn,stale:false});
  const worst=Math.max(...["DEC03","DEC05","DEC13"].map(d=>LEVEL_VALUE[sim.actual[d]]||0));
  return worst>=4?"航路・泊地・岸壁を再確認しましたが、重大な支障が残っています。現時点では受入を再開せず、応急復旧又は代替施設の確保を継続します。":worst>=3?"航路・泊地・岸壁を再確認しました。制約が残るため、船型・喫水・使用岸壁等を限定した受入再開条件を整理します。":"航路・泊地・岸壁を再確認しました。安全条件を満たすことを確認したうえで、対象船舶の受入再開を調整できます。"
 }
 return "船舶受入に必要な対応を実施しました。"
}
'''
if 'function requestShipAcceptanceResponses()' not in s:
 if anchor not in s: raise SystemExit('criticalFollowUpsBase anchor missing')
 s=s.replace(anchor,helper+anchor,1)

# Add pending routes to the normal critical-candidate pool.
needle='''  if(p.kind==="CARGO_FUNCTION_PRIORITY"&&cargoPriorityNeedsAction()){'''
insert='''  if(["SHIP_WAIT","SHIP_ALT_BERTH","SHIP_ALT_PORT","SHIP_REENTRY"].includes(p.kind)){
   const x=opt("DEC13","FOLLOW_UP",p.label);x.priority=p.priority||940;x.followUpKind=p.kind;o.push(x)
  }
'''
if insert.strip() not in s:
 if needle not in s: raise SystemExit('critical pool anchor missing')
 s=s.replace(needle,insert+needle,1)

# Guarantee presentation opportunity within normal four + reconsider cycles, without forcing all four into the first screen.
needle=''' if(x?.followUpKind==="POWER_CONTINUITY"||x?.followUpKind==="BERTH_RECOVERY_ALT"||x?.followUpKind==="ALT_BERTH_CHECK"||x?.followUpKind==="BERTH_RESOURCE_CHECK"||x?.followUpKind==="UTIL_CONDITION")return 1800+(x.priority||0);'''
replacement=needle+'''\n if(["SHIP_WAIT","SHIP_ALT_BERTH","SHIP_ALT_PORT","SHIP_REENTRY"].includes(x?.followUpKind))return 1725+(x.priority||0);'''
if 'SHIP_REENTRY"].includes(x?.followUpKind))return 1725' not in s:
 if needle not in s: raise SystemExit('required rank anchor missing')
 s=s.replace(needle,replacement,1)

# When DEC13 reports L4 / unsafe acceptance, register the four routes for subsequent choice generation.
needle=''' if(option.dec==="DEC10"&&["L0","L1"].includes(reported))text+="\\n必要な復旧作業へ資源を投入できる可能性があります。";'''
insert=''' if(option.dec==="DEC13"&&reported==="L4"){
  requestShipAcceptanceResponses();
  text+="\\n対象船舶の安全確保、別岸壁・受入条件、代替港調整、受入再開条件を状況に応じて判断する必要があります。"
 }
'''
if insert.strip() not in s:
 if needle not in s: raise SystemExit('inspect DEC10 anchor missing')
 s=s.replace(needle,insert+needle,1)

# Resolve the new choices in both direct and compressed batch paths.
needle='''  }else if(item.followUpKind==="TSUNAMI_EVAC"){resolveTsunamiEvacuation();lines.push(item.label+"：実施済み")}else if(item.followUpKind==="CARGO_FUNCTION_PRIORITY"){'''
replacement='''  }else if(["SHIP_WAIT","SHIP_ALT_BERTH","SHIP_ALT_PORT","SHIP_REENTRY"].includes(item.followUpKind)){
   resolveShipAcceptanceResponse(item);lines.push(item.label+"：対応済み")
  }else if(item.followUpKind==="TSUNAMI_EVAC"){resolveTsunamiEvacuation();lines.push(item.label+"：実施済み")}else if(item.followUpKind==="CARGO_FUNCTION_PRIORITY"){'''
if replacement not in s:
 if needle not in s: raise SystemExit('batch anchor missing')
 s=s.replace(needle,replacement,1)

needle='''  }else if(option.followUpKind==="CARGO_FUNCTION_PRIORITY"){'''
insert='''  }else if(["SHIP_WAIT","SHIP_ALT_BERTH","SHIP_ALT_PORT","SHIP_REENTRY"].includes(option.followUpKind)){
   const t=resolveShipAcceptanceResponse(option);sim.lastResult=null;
   addMessage("left","result",phaseLabel(),t,"船舶受入対応");
   sim.history.push({turn:sim.currentTurn,dec:"DEC13",label:option.label,special:option.followUpKind})
'''
if insert.strip() not in s:
 if needle not in s: raise SystemExit('handleDecision anchor missing')
 s=s.replace(needle,insert+needle,1)

assert 'Ver.3.29' in s
assert 'requestShipAcceptanceResponses' in s
assert 'resolveShipAcceptanceResponse' in s
p.write_text(s)
