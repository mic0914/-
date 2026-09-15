from pathlib import Path
p=Path('index.html')
s=p.read_text()
s=s.replace('Ver.3.27','Ver.3.28')
# Add a durable alternate-port progression state without disturbing existing altPlan fields.
anchor='function responseStatusText()'
helper='''function altPortProgress(){\n const a=sim?.altPlan||{};\n if(a.selected||a.finalized||a.decision||a.chosen||a.selectedPort)return 4;\n if(a.compared||a.comparisonDone||a.aChecked&&a.bChecked)return 3;\n if(a.surveyed||a.checked||a.A||a.B||a.a||a.b||sim?.altSurveyDone)return 2;\n if(a.active||a.started||sim?.altPlanActive)return 1;\n return 0\n}\nfunction altPortAlreadyConsidered(){return altPortProgress()>=2}\nfunction normalizeAltPortRepeatLabel(label){\n if(!altPortAlreadyConsidered())return label;\n if(label==="代替港A・Bの検討を開始します。")return "代替港A・Bの確認結果を継続利用します。";\n if(/代替港A・B.*検討を開始/.test(label))return label.replace(/検討を開始(?:します)?。?/,'条件を再確認する');\n return label\n}\n'''
if 'function altPortProgress()' not in s:
 s=s.replace(anchor,helper+anchor,1)
# Suppress the exact repeated result text globally at message rendering boundary.
for sig in ['function addMessage(side,type,title,text){','function addMessage(side,type,title,text) {']:
 if sig in s:
  s=s.replace(sig,sig+'\n text=normalizeAltPortRepeatLabel(String(text??""));',1);break
else: raise SystemExit('addMessage not found')
# Suppress repeated choice labels at choice rendering boundary too.
import re
m=re.search(r'function\s+(renderChoices|renderOptions)\s*\(([^)]*)\)\s*\{',s)
if m:
 pos=m.end(); arg=m.group(2).split(',')[0].strip() or 'options'
 inject=f'\n if(altPortAlreadyConsidered()&&Array.isArray({arg})){{{arg}={arg}.filter(x=>!(/代替港A・B.*検討を開始/.test(x?.label||""))).map(x=>x)}}'
 s=s[:pos]+inject+s[pos:]
# Exact old message must only be possible as source text but will be normalized at runtime.
assert 'Ver.3.28' in s and 'altPortAlreadyConsidered' in s and 'normalizeAltPortRepeatLabel' in s
p.write_text(s)
