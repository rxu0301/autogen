from app.services.script_service import _fallback_scripts, _count, DURATION_CONFIG

title = 'AI 기술 혁신'
content = 'AI 기술이 빠르게 발전하며 의료, 금융, 교육 등 다양한 분야에 영향을 미치고 있습니다.'

for lang in ['ko', 'en']:
    print(f'--- {lang.upper()} ---')
    for d in ['20초', '30초', '1분']:
        cfg = DURATION_CONFIG[d]
        r = _fallback_scripts(title, content, d, lang)
        s = r[0]
        cnt = _count(s.script, lang)
        unit = '자' if lang == 'ko' else 'words'
        if lang == 'ko':
            lo, hi = cfg['ko']['min'], cfg['ko']['max']
        else:
            lo, hi = cfg['en']['min_words'], cfg['en']['max_words']
        ok = '✅' if lo <= cnt <= hi else '❌'
        print(f'  {d}: 목표 {lo}~{hi}{unit} / 실제 {cnt}{unit} {ok}')
