from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

def rep(old,new,name,count=1):
    global s
    if old not in s:
        raise SystemExit(f'missing target: {name}')
    s=s.replace(old,new,count)

s=s.replace('Ver.3.24','Ver.3.25')

old=''' const gapText=gaps.length?gaps.map((x,i)=>`${i+1}. ${x}`).join("\\n"):"今回の被災条件と選択履歴を照合した範囲では、大きく不足した対応は確認されませんでした。";\n addMessage("left","score","不足していた対応",gapText+"\\n\\n※ Phase番号は、その対応候補が実際に提示された選択段階を示します。\\n※ その時点で必要な重要対応は、通常4択＋再検討3回の最大16候補内（多数時は一括確認を含む）に提示されます。追加EVENTで状況が変化した場合は新しい判断局面として再構成します。この欄は実際に提示された対応のみを対象とし、ここで追加の減点は行いません。");'''
new=''' let gapText="";\n if(gaps.length){\n  gapText=gaps.map((x,i)=>`${i+1}. ${x}`).join("\\n")\n }else if(g==="C"||g==="D"){\n  const reasons=[];\n  if(risk.penalty>0)reasons.push(`未確認重大リスクによる減点 －${risk.penalty.toFixed(1)}点`);\n  if(mistakes.penalty>0)reasons.push(`重大判断ミスによる減点 －${mistakes.penalty.toFixed(1)}点`);\n  if(tp>0)reasons.push(`時間超過による減点 －${tp.toFixed(1)}点`);\n  const componentDef=[];\n  if(core.total<48)componentDef.push(`基礎対応 ${core.total.toFixed(1)}/60`);\n  if(route<8)componentDef.push(`判断経路 ${route.toFixed(1)}/10`);\n  if(rec<8)componentDef.push(`復旧・代替 ${rec.toFixed(1)}/10`);\n  if(policy<4)componentDef.push(`最終方針 ${policy.toFixed(1)}/5`);\n  if(inf.risk+inf.conf<12)componentDef.push(`情報把握 ${(inf.risk+inf.conf).toFixed(1)}/15`);\n  if(componentDef.length)reasons.push(`対応力評価で低かった項目：${componentDef.join("・")}`);\n  gapText="提示された対応候補の中で、未実施の大きな対応は確認されませんでした。\\nただし、最終判定が"+g+"となった主な評価要因は次のとおりです。\\n"+(reasons.length?reasons.map((x,i)=>`${i+1}. ${x}`).join("\\n"):"・総合評価点が判定基準を下回りました。")\n }else{\n  gapText="今回の被災条件と選択履歴を照合した範囲では、大きく不足した対応は確認されませんでした。"\n }\n addMessage("left","score","不足していた対応",gapText+"\\n\\n※ Phase番号は、その対応候補が実際に提示された選択段階を示します。\\n※ その時点で必要な重要対応は、通常4択＋再検討3回の最大16候補内（多数時は一括確認を含む）に提示されます。追加EVENTで状況が変化した場合は新しい判断局面として再構成します。この欄は実際に提示された対応のみを対象とし、ここで追加の減点は行いません。");'''
rep(old,new,'gap verdict consistency')

p.write_text(s,encoding='utf-8')
print('patched Ver.3.25')
