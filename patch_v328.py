from pathlib import Path
import re
p=Path('index.html')
s=p.read_text()
s=s.replace('Ver.3.27','Ver.3.28')
anchor='function responseStatusText()'
helper='''function altPortProgress(){
 const a=sim?.altPorts;
 if(!a?.activated)return 0;
 const ports=Object.values(a.ports||{});
 if(ports.some(p=>p.known?.cargo))return 4;
 if(ports.some(p=>p.known?.coordinated!==null&&p.known?.coordinated!==undefined))return 3;
 if(a.surveyCompleted||ports.some(p=>p.known?.summary||p.known?.detail||p.known?.access))return 2;
 return 1
}
function altPortAlreadyConsidered(){return altPortProgress()>=2}
function normalizeAltPortRepeatLabel(label){
 if(!altPortAlreadyConsidered())return label;
 if(label==="代替港A・Bの検討を開始します。")return "代替港A・Bの確認済み情報を継続して判断に使用します。";
 if(/代替港A・B.*検討を開始/.test(label))return label.replace(/検討を開始(?:します)?。?/,'確認済み条件を再確認する');
 return label
}
'''
if 'function altPortProgress()' not in s:
 if anchor not in s: raise SystemExit('responseStatusText anchor not found')
 s=s.replace(anchor,helper+anchor,1)
# Match addMessage regardless of extra parameters/spacing.
m=re.search(r'function\s+addMessage\s*\(([^)]*)\)\s*\{',s)
if not m: raise SystemExit('addMessage function not found')
if 'normalizeAltPortRepeatLabel(String(text' not in s:
 pos=m.end();s=s[:pos]+'\n text=normalizeAltPortRepeatLabel(String(text??""));'+s[pos:]
# When A/B survey has already been completed, do not present a choice that restarts consideration.
m=re.search(r'function\s+renderOptions\s*\(([^)]*)\)\s*\{',s)
if not m: raise SystemExit('renderOptions function not found')
if 'altPortAlreadyConsidered()&&Array.isArray(options)' not in s:
 pos=m.end();s=s[:pos]+'\n if(altPortAlreadyConsidered()&&Array.isArray(options))options=options.filter(x=>!(/代替港A・B.*検討を開始/.test(x?.label||"")));'+s[pos:]
assert 'Ver.3.28' in s
assert 'sim?.altPorts' in s
assert 'normalizeAltPortRepeatLabel' in s
assert 'altPortAlreadyConsidered()&&Array.isArray(options)' in s
p.write_text(s)
