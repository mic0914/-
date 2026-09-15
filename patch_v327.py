from pathlib import Path
p=Path('index.html')
s=p.read_text()
s=s.replace('Ver.3.26','Ver.3.27')
texts=[
'Phase番号は、その対応候補が実際に提示された選択段階を示します。',
'※ その時点で必要な重要対応は、通常4択＋再検討3回の最大16候補内（多数時は一括確認を含む）に提示されます。追加EVENTで状況が変化した場合は新しい判断局面として再構成します。この欄は実際に提示された対応のみを対象とし、ここで追加の減点は行いません。'
]
for t in texts:
 s=s.replace('\\n'+t,'').replace(t+'\\n','').replace(t,'')
assert 'Ver.3.27' in s
for t in texts: assert t not in s
p.write_text(s)
# retrigger after successful Ver.3.26 patch
