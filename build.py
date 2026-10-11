#!/usr/bin/env python3
"""Builds the second Afnan site into dist/ from content/ (edited in the dashboard) and templates/.
Standard library only, so Cloudflare can run it with `python3 build.py`."""
import json, glob, html, re, os, shutil, urllib.parse
ROOT = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(ROOT, 'content') + '/'
T = os.path.join(ROOT, 'templates') + '/'
OUT = os.path.join(ROOT, 'dist') + '/'
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(os.path.join(ROOT, 'static'), OUT)
shutil.copytree(os.path.join(ROOT, 'admin'), OUT + 'admin')
esc = lambda s: html.escape(str(s or ''), quote=True)
def load(n): return json.load(open(C + n + '.json', encoding='utf-8'))
def img(p): return (p or '').lstrip('/')
def num(v, d=99):
    try: return float(v)
    except Exception: return d
def folder(n):
    out = []
    for f in sorted(glob.glob(C + n + '/*.json')):
        d = json.load(open(f, encoding='utf-8'))
        if d.get('hidden'): continue
        d['slug'] = re.sub(r'[^a-z0-9-]+', '-', str(d.get('url') or os.path.splitext(os.path.basename(f))[0]).lower()).strip('-')
        out.append(d)
    return sorted(out, key=lambda d: num(d.get('order')))
SET = load('settings')

# ---------------------------------------------------------------- markdown
def inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|[\w./#-]+)\)", r'<a href="\2">\1</a>', t)
    return t

def markdown(md):
    out = []
    for block in re.split(r"\n\s*\n", str(md or "").strip()):
        lines = [l.rstrip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        if re.match(r"^#{1,4}\s", lines[0]) and len(lines) == 1:
            out.append("<h3>" + inline(re.sub(r"^#{1,4}\s+", "", lines[0])) + "</h3>")
        elif all(re.match(r"^\s*[-*]\s+", l) for l in lines):
            out.append("<ul>" + "".join("<li>" + inline(re.sub(r"^\s*[-*]\s+", "", l)) + "</li>" for l in lines) + "</ul>")
        else:
            if re.match(r"^#{1,4}\s", lines[0]):
                out.append("<h3>" + inline(re.sub(r"^#{1,4}\s+", "", lines[0])) + "</h3>")
                lines = lines[1:]
            if lines:
                out.append("<p>" + inline(" ".join(lines)) + "</p>")
    return "".join(out)

# ------------------------------------------------------------------ home page pieces

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=El+Messiri:wght@500;600;700&display=swap">'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap">')
BOOT = "<script>(function(d){d.classList.add('js');try{if(sessionStorage.getItem('afnSeen'))d.classList.add('seen')}catch(e){}})(document.documentElement)</script>"
GSAP = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>\n'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>')

# ---------------------------------------------------------------- data
SECTIONS = [("med", "الخدمات الطبية"), ("nurse", "التمريض المنزلي"), ("elder", "كبار السن وذوو الهمم"), ("kids", "الأم والطفل"),
            ("rehab", "العلاج الطبيعي والتأهيل"), ("lab", "التحاليل المنزلية"), ("food", "التغذية العلاجية"), ("car", "النقل الطبي")]
SECNAME = dict(SECTIONS)
svcs = folder('services')
for d in svcs:
    d['img'] = img(d.get('image')) or 'img/n/svc-nursing.jpg'
    d['includes'] = [x if isinstance(x, str) else x.get('item', '') for x in (d.get('includes') or [])]
    d['suitable_for'] = [x if isinstance(x, str) else x.get('item', '') for x in (d.get('suitable_for') or [])]
    if d.get('section') not in SECNAME: d['section'] = 'nurse'
page = lambda d: 's-%s.html' % d['slug']
BYSLUG = {d['slug']: d for d in svcs}

# ---------------------------------------------------------------- shared pieces from the home body
body = open(T + 'home.html', encoding='utf-8').read()
TOP = body[body.index('<header class="tb"'):body.index('</header>') + 9]
DOCK = body[body.index('<div class="scrim"'):body.index('<div class="reader"')]
FOOT = body[body.index('<footer class="ft">'):body.index('</footer>') + 9]

def mark(sz):
    return f'<svg class="mark-ic" width="{sz}" height="{sz}" viewBox="0 0 64 64" aria-hidden="true"><g fill="none" stroke="#c9a24e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 52V30a16 16 0 0 1 32 0v22"/><path d="M32 46c-6-4.2-10-7.6-10-12a5.2 5.2 0 0 1 10-2 5.2 5.2 0 0 1 10 2c0 4.4-4 7.8-10 12z"/><path class="pulse" d="M12 52h14l3-5 4 9 3-6 3 2h13"/></g></svg>'
DOCK = DOCK.replace('{{MARK44}}', mark(44)).replace('{{MARK46}}', mark(46))
STORIES = load('stories').get('stories', [])
st_data = json.dumps([{'t': s.get('label', ''), 'img': img(s.get('image')), 'h': s.get('title', ''), 'p': s.get('text', ''), 'href': s.get('link', 'index.html'), 'cta': s.get('button', 'التفاصيل')} for s in STORIES], ensure_ascii=False)
SV = f'''<div class="sv" id="sv" role="dialog" aria-modal="true" aria-label="قصص أفنان" aria-hidden="true"><div class="sv-bars" id="svBars"></div><img class="sv-img" id="svImg" src="" alt=""><div class="sv-shade"></div><button class="sv-x" id="svX" type="button" aria-label="إغلاق">×</button><div class="sv-tap sv-p" id="svPrev"></div><div class="sv-tap sv-n" id="svNext"></div><div class="sv-copy"><small id="svT"></small><b id="svH"></b><p id="svP"></p><a class="btn" id="svCta" href="#">.</a></div></div>
<script>window.AFN_STORIES={st_data};</script>'''
DOCK = DOCK + SV


pay = ['mada', 'visa', 'applepay', 'stcpay', 'tabby', 'tamara', 'hala', 'sab', 'sifi']
FOOT = FOOT.replace('{{PAY}}', ''.join(f'<span><img src="img/pay/{p}.png" alt="{p}" loading="lazy"></span>' for p in pay))
foot_svcs = ['home-nursing', 'elderly-care', 'home-physiotherapy', 'home-lab-tests', 'infant-care', 'home-doctor-visits']
FOOT = re.sub(r'<div><h4>خدماتنا</h4><ul>.*?</ul></div>',
              '<div><h4>خدماتنا</h4><ul>' + ''.join(f'<li><a href="{page(BYSLUG[s])}">{esc(BYSLUG[s]["title"])}</a></li>' for s in foot_svcs if s in BYSLUG) + '<li><a href="services.html">كل الخدمات ←</a></li></ul></div>', FOOT, flags=re.S)
def foot_links(home):
    p = '' if home else 'index.html'
    return re.sub(r'<div><h4>روابط</h4><ul>.*?</ul></div>',
                  f'<div><h4>روابط</h4><ul><li><a href="about.html">من نحن</a></li><li><a href="{p}#programs">برامج الرعاية</a></li><li><a href="{p}#guide">دليلك الصحي</a></li><li><a href="{p}#faq">الأسئلة الشائعة</a></li><li><a href="partners.html">الشراكات</a></li></ul></div>', FOOT, flags=re.S
                  ).replace('<a href="#">سياسة الخصوصية</a> · <a href="#">الشروط والأحكام</a>', '<a href="privacy.html">سياسة الخصوصية</a> · <a href="terms.html">الشروط والأحكام</a>')

def top(home):
    t = re.sub(r'<a href="#hero" aria-label="[^"]*"><img src="img/mark.png" alt="شعار أفنان الفائقة"></a>', '<button class="logo-st" id="logoSt" type="button" aria-label="قصص أفنان، اضغط للمشاهدة"><span class="st-ring" aria-hidden="true"></span><img src="img/mark.png" alt=""><span class="st-badge" aria-hidden="true">'+str(len(STORIES))+'</span></button>', TOP)
    t = t.replace('<a class="l" href="#services">الخدمات</a>', '<a class="l" href="services.html">الخدمات</a>')
    t = t.replace('<a class="l" href="#partners">الشراكات</a>', '<a class="l" href="partners.html">الشراكات</a>')
    if not home:
        t = t.replace('href="#programs"', 'href="index.html#programs"').replace('href="#guide"', 'href="index.html#guide"').replace('href="#hero"', 'href="index.html"')
    return t

def secs(links):
    a = ''.join(f'<a href="{h}">{t}</a>' for h, t in links)
    return re.sub(r'<nav class="secs" id="secs" aria-label="أقسام الصفحة" aria-hidden="true">.*?</nav>',
                  f'<nav class="secs" id="secs" aria-label="أقسام الموقع" aria-hidden="true">{a}</nav>', DOCK, flags=re.S)

INNER_SECS = [('index.html', 'الرئيسية'), ('services.html', 'كل الخدمات'), ('about.html', 'من نحن'), ('index.html#programs', 'برامج الرعاية'),
              ('index.html#guide', 'دليلك الصحي'), ('index.html#faq', 'الأسئلة الشائعة'), ('partners.html', 'الشراكات')]
PT = '<div class="ptr cover" id="pt" aria-hidden="true"><span class="pm"><img src="img/mark.png" alt=""></span></div>'

def end_cta(title='جاهزين نخدمكم، اليوم.', svc=''):
    db = f' data-book="{esc(svc)}"' if svc else ' data-book'
    return f'''<section class="end" aria-label="احجز" data-ctx="احجز الآن">
    <span class="arch"></span><span class="arch two"></span>
    <div class="wrap">
      <span class="eyebrow rvl">احجز الآن</span>
      <h2 class="rvl d1">{title}</h2>
      <p class="rvl d2">احجزوا من الشاشة في دقيقة، أو اتصلوا علينا مباشرة. نرتّب معكم الزيارة في أي منطقة من المملكة.</p>
      <button class="btn wa rvl d3" type="button"{db} style="border:0;font:inherit;font-weight:600;font-size:17px;cursor:pointer">احجز زيارة <span class="arr" aria-hidden="true">←</span></button>
      <span class="phone">أو اتصلوا على <b>+966 55 518 5244</b></span>
    </div>
  </section>'''

def write_inner(name, title, desc, main, secs_links=INNER_SECS, extra_js=''):
    doc = f'''<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)} · أفنان الفائقة</title><meta name="description" content="{esc(desc)}">
{BOOT}
{FONTS}
<link rel="stylesheet" href="s2.css">
</head><body>
{PT}
{top(False)}
<main>
{main}
</main>
{foot_links(False)}
{secs(secs_links)}
<script src="core.js"></script>
<script src="stories.js"></script>
{extra_js}
</body></html>
'''
    open(OUT + name, 'w', encoding='utf-8').write(doc)

def card(d, cls='sc'):
    return (f'<a class="{cls} rvl" href="{page(d)}" data-sec="{d["section"]}"><span class="ph"><img src="{d["img"]}" alt="" loading="lazy"></span>'
            f'<small>{esc(SECNAME[d["section"]])}</small><h3>{esc(d["title"])}</h3><p>{esc(d["description"])}</p><span class="more">التفاصيل <span>←</span></span></a>')

CHIPS = '<div class="chips rvl d2"><span>كوادر مرخّصة</span><span>على مدار الساعة</span><span>جميع مناطق المملكة</span><span>ممرض أو ممرضة</span></div>'
FLOW = '''<section class="flow" aria-label="كيف تتم الزيارة" data-ctx="ابدأ الخطوة الأولى">
  <div class="wrap"><span class="eyebrow rvl">كيف تتم الزيارة</span><h2 class="rvl d1">أربع خطوات، وكل شيء واضح</h2>
  <div class="flow-row">
    <div class="fs rvl"><i>1</i><b>تحجزون أو تتصلون</b><span>من شاشة الحجز أو باتصال مباشر.</span></div>
    <div class="fs rvl d1"><i>2</i><b>نقيّم الحالة</b><span>مختص يقترح الخدمة والكادر المناسب.</span></div>
    <div class="fs rvl d2"><i>3</i><b>يصلكم الكادر</b><span>مرخّص، بأدوات معقّمة وفي الموعد.</span></div>
    <div class="fs rvl d3"><i>4</i><b>متابعة وتقرير</b><span>تقرير بعد كل زيارة وخطة واضحة.</span></div>
  </div></div>
</section>'''

# ---------------------------------------------------------------- service pages
for d in svcs:
    rel = [x for x in svcs if x['section'] == d['section'] and x['slug'] != d['slug']]
    rel += [x for x in svcs if x['section'] != d['section'] and x not in rel]
    rel = rel[:3]
    inc = ''.join(f'<div>{esc(i)}</div>' for i in d['includes'])
    fit = ''.join(f'<span>{esc(i)}</span>' for i in d['suitable_for'])
    main = f'''<section class="ih light" data-ctx="احجز {esc(d['title'])}">
    <div class="wrap ih-grid">
      <div>
        <nav class="crumb rvl" aria-label="مسار الصفحة"><a href="index.html">الرئيسية</a><span>/</span><a href="services.html">الخدمات</a><span>/</span><a href="services.html#{d['section']}">{esc(SECNAME[d['section']])}</a></nav>
        <span class="eyebrow rvl">{esc(SECNAME[d['section']])}</span>
        <h1 class="rvl d1" style="color:var(--navy)">{esc(d['title'])}</h1>
        <p class="lead rvl d2">{esc(d['description'])} نصلكم في الوقت اللي يناسبكم، بأدوات معقّمة وتقرير بعد كل زيارة.</p>
        {CHIPS}
        <div class="acts rvl d3"><button class="btn dark mag" type="button" data-book="{esc(d['title'])}" style="border:0;font:inherit;font-weight:600;font-size:17px;cursor:pointer">احجز هذه الخدمة <span class="arr" aria-hidden="true">←</span></button><a class="ghost dark" href="tel:+966555185244">اتصل الآن</a></div>
      </div>
      <div class="ih-ph rv-clip"><img src="{d['img']}" alt="{esc(d['title'])} في المنزل مع فريق أفنان"></div>
    </div>
  </section>
  <section class="blk paper" data-ctx="احجز {esc(d['title'])}">
    <div class="wrap two">
      <div><span class="eyebrow rvl">ماذا تشمل الخدمة</span><h2 class="rvl d1">كل اللي تحتاجه الحالة، في زيارة وحدة</h2><div class="inc rvl d2">{inc}</div></div>
      <div><span class="eyebrow rvl">لمن تناسب</span><h2 class="rvl d1">مناسبة لـ</h2><div class="fit rvl d2">{fit}</div></div>
    </div>
  </section>
  {FLOW}
  <section class="blk ivory" data-ctx="أي خدمة تحتاجونها؟">
    <div class="wrap">
      <div class="head-row"><div><span class="eyebrow rvl">خدمات قريبة</span><h2 class="rvl d1">قد تحتاجون أيضًا</h2></div><a class="lnk rvl" href="services.html">كل الخدمات ←</a></div>
      <div class="rel">{''.join(card(x) for x in rel)}</div>
    </div>
  </section>
  {end_cta('نرتّب لكم ' + esc(d['title']) + '، اليوم.', d['title'])}'''
    write_inner(page(d), d['title'], f"{d['title']} من مركز أفنان الفائقة: {d['description']} على مدار الساعة في جميع مناطق المملكة.", main)

# ---------------------------------------------------------------- services hub
counts = {k: sum(1 for d in svcs if d['section'] == k) for k, _ in SECTIONS}
fl = '<button class="fl on" type="button" data-f="all">الكل<small>' + str(len(svcs)) + '</small></button>' + ''.join(
    f'<button class="fl" type="button" data-f="{k}">{n}<small>{counts[k]}</small></button>' for k, n in SECTIONS)
hub_main = f'''<section class="ih" data-ctx="أي خدمة تحتاجونها؟" style="padding-bottom:70px">
    <div class="wrap">
      <nav class="crumb rvl" aria-label="مسار الصفحة"><a href="index.html">الرئيسية</a><span>/</span><span style="opacity:1">الخدمات</span></nav>
      <span class="eyebrow rvl">خدماتنا</span>
      <h1 class="rvl d1">كل خدماتنا، في مكان واحد</h1>
      <p class="lead rvl d2">{len(svcs)} خدمة طبية وتمريضية وتأهيلية في البيت، مقسّمة على ثمانية أقسام. اختاروا القسم، أو تصفحوا الكل.</p>
    </div>
  </section>
  <div class="filters"><div class="wrap" role="toolbar" aria-label="تصفية حسب القسم">{fl}</div></div>
  <section class="blk ivory" data-ctx="احجز زيارة في دقيقة" style="padding-top:44px">
    <div class="wrap"><p class="hub-count" id="hubCount" aria-live="polite">{len(svcs)} خدمة</p><div class="hub" id="hub">{''.join(card(d) for d in svcs)}</div></div>
  </section>
  {end_cta()}'''
hub_js = '''<script>
(function(){var hub=document.getElementById("hub"),cards=[].slice.call(hub.children),cnt=document.getElementById("hubCount"),btns=[].slice.call(document.querySelectorAll(".fl"));
function apply(f,scroll){btns.forEach(function(b){b.classList.toggle("on",b.dataset.f===f);b.setAttribute("aria-pressed",b.dataset.f===f?"true":"false")});
 var n=0;cards.forEach(function(c){var show=f==="all"||c.dataset.sec===f;if(show)n++;c.classList.add("out");});
 setTimeout(function(){cards.forEach(function(c){var show=f==="all"||c.dataset.sec===f;c.hidden=!show;if(show){c.classList.add("in");requestAnimationFrame(function(){c.classList.remove("out")})}})},220);
 cnt.textContent=n+" خدمة";if(scroll){var y=hub.getBoundingClientRect().top+scrollY-170;if(scrollY>y)scrollTo({top:y,behavior:"smooth"})}
 try{history.replaceState(null,"",f==="all"?location.pathname:"#"+f)}catch(e){}}
btns.forEach(function(b){b.addEventListener("click",function(){apply(b.dataset.f,true);b.scrollIntoView({block:"nearest",inline:"center",behavior:"smooth"})})});
var h=(location.hash||"").slice(1);if(h&&btns.some(function(b){return b.dataset.f===h}))apply(h,false);})();
</script>'''
write_inner('services.html', 'كل الخدمات', 'خدمات أفنان الفائقة الطبية المنزلية: زيارات الأطباء، التمريض، كبار السن، الأم والطفل، العلاج الطبيعي، التحاليل، التغذية والنقل الطبي.', hub_main, extra_js=hub_js)

# ---------------------------------------------------------------- about
about_main = f'''<section class="ih" data-ctx="احجز زيارة في دقيقة">
    <div class="wrap ih-grid">
      <div>
        <nav class="crumb rvl" aria-label="مسار الصفحة"><a href="index.html">الرئيسية</a><span>/</span><span style="opacity:1">من نحن</span></nav>
        <span class="eyebrow rvl">عن أفنان الفائقة</span>
        <h1 class="rvl d1">فريق صحي متكامل، يجيكم لين باب البيت</h1>
        <p class="lead rvl d2">مركز أفنان الفائقة للخدمات الطبية المنزلية يقدّم رعاية طبية وتمريضية وتأهيلية داخل المنزل، بكوادر مرخّصة وأدوات معقّمة. نصمّم الرعاية حسب حالة كل مريض واحتياج أسرته، ونتابع معكم بتقارير واضحة.</p>
        <div class="acts rvl d3"><button class="btn mag" type="button" data-book style="border:0;font:inherit;font-weight:600;font-size:17px;cursor:pointer">احجز زيارة <span class="arr" aria-hidden="true">←</span></button><a class="ghost" href="services.html">تصفّح الخدمات</a></div>
      </div>
      <div class="ih-ph rv-clip"><img src="img/n/prg-elderly.jpg" alt="مرافِقة من أفنان تمشي مع سيدة كبيرة في السن"></div>
    </div>
    <div class="wrap" style="margin-top:70px"><div class="nums" id="nums">
      <div class="rvl"><b data-n="150" data-p="+">+150</b><span>طبيب وممرض وأخصائي</span></div>
      <div class="rvl d1"><b data-n="13">13</b><span>منطقة في المملكة</span></div>
      <div class="rvl d2"><b>24/7</b><span>على مدار الساعة</span></div>
      <div class="rvl d3"><b data-n="{len(svcs)}">{len(svcs)}</b><span>خدمة منزلية</span></div>
    </div></div>
  </section>
  <section class="say" aria-label="رسالتنا" data-ctx="تبون نجيكم البيت؟">
    <div class="wrap">
      <span class="eyebrow rvl" style="color:var(--gold-deep)">ليش البيت؟</span>
      <p class="rvl d1" style="margin-top:22px">نؤمن أن أفضل مكان للتعافي هو البيت، بين أهلك وقريب من اللي تحبهم. لذلك نجيب الرعاية لعندك، بنفس الدقة اللي تلقاها في المستشفى.</p>
      <div class="pts">
        <div class="pt rvl"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg><b>كوادر مرخّصة</b><span>أطباء وممرضون وأخصائيون مدرّبون على الرعاية المنزلية.</span></div>
        <div class="pt rvl d1"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M14.5 14.5c3 0 6.5 1.5 6.5 5.5"/></svg><b>ممرض أو ممرضة</b><span>حسب تفضيلكم وحالة المريض.</span></div>
        <div class="pt rvl d2"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M5 12h14M12 5v14"/><circle cx="12" cy="12" r="9"/></svg><b>أدوات معقّمة</b><span>في كل زيارة، وبمعايير المنشآت الصحية.</span></div>
        <div class="pt rvl d3"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18M7 15h4"/></svg><b>الدفع بعد الخدمة</b><span>خلال 24 ساعة من تقديمها، بالطريقة اللي تناسبكم.</span></div>
      </div>
    </div>
  </section>
  {FLOW}
  <section class="blk ivory" data-ctx="أي خدمة تحتاجونها؟">
    <div class="wrap">
      <div class="head-row"><div><span class="eyebrow rvl">خدماتنا</span><h2 class="rvl d1">من المولود، إلى الوالدين في كبرهم</h2></div><a class="lnk rvl" href="services.html">كل الخدمات ←</a></div>
      <div class="rel">{''.join(card(BYSLUG[s]) for s in ['home-nursing', 'elderly-care', 'infant-care'] if s in BYSLUG)}</div>
    </div>
  </section>
  {end_cta()}'''
count_js = '''<script>
(function(){if(!("IntersectionObserver" in window)||matchMedia("(prefers-reduced-motion: reduce)").matches)return;
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;io.unobserve(e.target);var el=e.target,n=+el.dataset.n,p=el.dataset.p||"",t0=performance.now();
(function f(t){var k=Math.min(1,(t-t0)/1600),v=Math.round(n*(1-Math.pow(1-k,3)));el.textContent=p+v;if(k<1)requestAnimationFrame(f)})(t0)})},{threshold:.6});
document.querySelectorAll("#nums b[data-n]").forEach(function(b){b.textContent=(b.dataset.p||"")+"0";io.observe(b)})})();
</script>'''
write_inner('about.html', 'من نحن', 'تعرّف على مركز أفنان الفائقة للخدمات الطبية المنزلية: فريق مرخّص يقدّم الرعاية الطبية والتمريضية والتأهيلية في البيت.', about_main, extra_js=count_js)

# ---------------------------------------------------------------- partners
WA_P = 'https://wa.me/966555185244?text=' + __import__('urllib.parse').parse.quote('السلام عليكم، أرغب في التواصل مع فريق الشراكات')
def ic(p): return f'<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">{p}</svg>'
ptn_main = f'''<section class="ih" data-ctx="تواصلوا مع فريق الشراكات">
    <div class="wrap ih-grid">
      <div>
        <nav class="crumb rvl" aria-label="مسار الصفحة"><a href="index.html">الرئيسية</a><span>/</span><span style="opacity:1">الشراكات</span></nav>
        <span class="eyebrow rvl">للشركات والمستشفيات</span>
        <h1 class="rvl d1">شريككم في استكمال الرعاية بعد خروج المريض</h1>
        <p class="lead rvl d2">نتعاون مع المستشفيات والعيادات وشركات التأمين والجهات، لنكمل رعاية مرضاكم ومنسوبيكم في بيوتهم بنفس المستوى، وبتقارير واضحة لكل حالة.</p>
        <div class="acts rvl d3"><a class="btn mag" href="{WA_P}" target="_blank" rel="noopener">تواصل مع فريق الشراكات <span class="arr" aria-hidden="true">←</span></a></div>
      </div>
      <div class="ih-ph rv-clip"><img src="img/n/partners2.jpg" alt="اجتماع شراكة بين فريق أفنان وشركاء من القطاع الصحي"></div>
    </div>
  </section>
  <section class="blk ivory" data-ctx="تواصلوا مع فريق الشراكات">
    <div class="wrap">
      <span class="eyebrow rvl">مع من نعمل</span><h2 class="rvl d1">شراكات تخدم المريض قبل كل شيء</h2>
      <div class="ptypes">
        <div class="ptype rvl">{ic('<path d="M4 21V8l8-5 8 5v13"/><path d="M9 21v-6h6v6M12 8v4M10 10h4"/>')}<b>المستشفيات والعيادات</b><p>إحالة المرضى بعد العمليات والخروج، مع متابعة تمريضية منزلية وتقرير يصل للطبيب المعالج.</p></div>
        <div class="ptype rvl d1">{ic('<path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6l7-3z"/>')}<b>شركات التأمين</b><p>رعاية منزلية لحاملي الوثائق، تخفف من أيام التنويم وتحافظ على راحة المريض.</p></div>
        <div class="ptype rvl d2">{ic('<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>')}<b>الشركات والجهات</b><p>برامج رعاية لمنسوبيكم وأسرهم، من الزيارات الطبية إلى التحاليل في البيت.</p></div>
        <div class="ptype rvl d3">{ic('<path d="M3 21h18M5 21V9l7-5 7 5v12"/><path d="M9 21v-4h6v4"/>')}<b>المجمعات السكنية</b><p>خدمات صحية قريبة من السكان، بزيارات منظّمة وتنسيق مع إدارة المجمع.</p></div>
      </div>
    </div>
  </section>
  <section class="flow" aria-label="كيف تبدأ الشراكة" data-ctx="تواصلوا مع فريق الشراكات">
    <div class="wrap"><span class="eyebrow rvl">كيف نبدأ</span><h2 class="rvl d1">من أول تواصل إلى أول إحالة</h2>
    <div class="flow-row">
      <div class="fs rvl"><i>1</i><b>تواصل</b><span>رسالة أو اتصال مع فريق الشراكات.</span></div>
      <div class="fs rvl d1"><i>2</i><b>اجتماع تعريفي</b><span>نفهم احتياجكم ونوع الحالات.</span></div>
      <div class="fs rvl d2"><i>3</i><b>اتفاق واضح</b><span>نطاق الخدمات وآلية الإحالة والتقارير.</span></div>
      <div class="fs rvl d3"><i>4</i><b>بدء الخدمة</b><span>إحالات منظّمة وتقارير دورية لكل حالة.</span></div>
    </div></div>
  </section>
  <section class="end" aria-label="تواصل" data-ctx="تواصلوا مع فريق الشراكات">
    <span class="arch"></span><span class="arch two"></span>
    <div class="wrap"><span class="eyebrow rvl">فريق الشراكات</span><h2 class="rvl d1">خلّونا نكمل الرعاية معكم.</h2>
      <p class="rvl d2">أرسلوا لنا رسالة على واتساب، ويتواصل معكم فريق الشراكات لترتيب اجتماع تعريفي.</p>
      <a class="btn wa mag rvl d3" href="{WA_P}" target="_blank" rel="noopener">راسل فريق الشراكات <span class="arr" aria-hidden="true">←</span></a>
      <span class="phone">أو اتصلوا على <b>+966 55 518 5244</b></span></div>
  </section>'''
write_inner('partners.html', 'الشراكات', 'شراكات أفنان الفائقة مع المستشفيات والعيادات وشركات التأمين والجهات لاستكمال رعاية المرضى في بيوتهم.', ptn_main)

# ---------------------------------------------------------------- legal
for f in glob.glob(T + 'legal/*.html'):
    raw = open(f, encoding='utf-8').read()
    t = re.search(r'<!-- title: (.*?) -->', raw).group(1); dsc = re.search(r'<!-- description: (.*?) -->', raw).group(1)
    content = re.sub(r'<!--.*?-->\n?', '', raw).replace('+966 55 518 5244', '+966 55 518 5244')
    main = f'''<section class="ih" style="padding-bottom:60px" data-ctx="احجز زيارة في دقيقة"><div class="wrap">
      <nav class="crumb rvl" aria-label="مسار الصفحة"><a href="index.html">الرئيسية</a><span>/</span><span style="opacity:1">{esc(t)}</span></nav>
      <h1 class="rvl d1">{esc(t)}</h1><p class="lead rvl d2" style="margin:0">{esc(dsc)}</p></div></section>
    <section class="blk paper" data-ctx="احجز زيارة في دقيقة"><div class="wrap"><div class="legal">{content}</div></div></section>'''
    write_inner(os.path.basename(f), t, dsc, main)

# ---------------------------------------------------------------- home
hb = body
H = load('hero')
gold = esc(H.get('title_gold', ''))
words = lambda s, cls='': ' '.join(f'<span class="w{cls}">{esc(w)}</span>' for w in str(s).split())
hb = hb.replace('{{HERO_EYEBROW}}', esc(H.get('eyebrow', ''))).replace('{{HERO_TEXT}}', esc(H.get('text', ''))).replace('{{HERO_IMAGE}}', esc(img(H.get('image'))))
hb = hb.replace('{{HERO_TITLE}}', f'<span class="ln">{words(H.get("title_1", ""))}</span><span class="ln">{words(H.get("title_2", ""))} {words(H.get("title_gold", ""), " gold")}</span>')
feat = sorted([d for d in svcs if d.get('featured')], key=lambda d: num(d.get('featured_order'))) or svcs[:6]
hb = hb.replace('{{HS_COUNT}}', '%02d' % len(feat))
hb = hb.replace('{{HOME_SERVICES}}', ''.join(f'\n        <a class="card" href="s-{d["slug"]}.html"><div class="ph clip"><img src="{esc(d["img"])}" alt="{esc(d["title"])}" loading="lazy"></div><div><span class="no">{i+1:02d}</span><h3>{esc(d["title"])}</h3><p>{esc(d["description"])}</p><span class="more">التفاصيل <span>←</span></span></div></a>' for i, d in enumerate(feat)))
PR = load('programs').get('programs', [])
hb = hb.replace('{{PROGRAMS}}', ''.join(f'\n        <article class="pc"><div class="tx"><div><span class="no">برنامج {i+1:02d}</span><h3>{esc(p.get("title"))}</h3><p>{esc(p.get("text"))}</p></div><div class="meta"><span class="dur">{esc(p.get("duration"))}</span><button class="ask" type="button" data-book="{esc(p.get("service"))}">اسأل عن البرنامج</button></div></div><div class="ph"><img src="{esc(img(p.get("image")))}" alt="" loading="lazy"></div></article>' for i, p in enumerate(PR)))
hb = hb.replace(TOP, top(True))
hb = hb.replace(FOOT_ORIG := body[body.index('<footer class="ft">'):body.index('</footer>') + 9], foot_links(True))
HOME_SECS = [('#hero', 'الرئيسية'), ('#services', 'الخدمات'), ('#programs', 'البرامج'), ('#about', 'عن أفنان'), ('#journey', 'كيف نعمل'),
             ('#guide', 'دليلك الصحي'), ('#faq', 'الأسئلة الشائعة'), ('services.html', 'كل الخدمات ←'), ('partners.html', 'الشراكات ←')]
hb = hb.replace(DOCK_ORIG := body[body.index('<div class="scrim"'):body.index('<div class="reader"')], secs(HOME_SECS))
hb = hb.replace('<div class="curtain" id="curtain" aria-hidden="true">', '<div class="ptr home" id="pt" aria-hidden="true"><span class="pm"><img src="img/mark.png" alt=""></span></div>\n<div class="curtain" id="curtain" aria-hidden="true">', 1)
hb = hb.replace('احجز الخدمة <span>←</span>', 'التفاصيل <span>←</span>')
hb = hb.replace('<div class="svc-side">', '<div class="svc-side"><a class="lnk" href="services.html" style="white-space:nowrap">كل الخدمات ←</a>', 1)
# reviews, faq, cities, articles, pay
rev = json.load(open(C + 'reviews.json', encoding='utf-8'))['reviews']
hb = hb.replace('{{REVIEWS}}', ''.join(f'<figure class="rv-item" style="margin:0"><p>{esc(r["text"])}</p><cite>{esc(r["name"])}</cite></figure>' for r in rev))
faq = json.load(open(C + 'faq.json', encoding='utf-8'))['faq']
hb = hb.replace('{{FAQ}}', ''.join(f'<div class="qa"><button type="button" aria-expanded="false"><b>{esc(q["q"])}</b><span class="pm" aria-hidden="true"></span></button><div class="ans"><div><p>{esc(q["a"])}</p></div></div></div>' for q in faq))
cities = ["الرياض", "جدة", "مكة المكرمة", "المدينة المنورة", "الدمام", "الخبر", "الطائف", "أبها", "بريدة", "تبوك", "حائل", "جازان", "نجران", "الأحساء", "ينبع"]
row = ''.join(f'<span>{c}</span>' for c in cities)
hb = hb.replace('{{CITIES}}', '<span class="h">نخدمكم في</span>' + row + '<span class="h">نخدمكم في</span>' + row)
ARTS = folder('articles')
order = [a['slug'] for a in ARTS]
arts = {}; acards = []; EXC = {}
for a in ARTS:
    k = a['slug']; EXC[k] = a.get('excerpt', '')
    arts[k] = {'title': a['title'], 'label': a.get('label', ''), 'minutes': a.get('minutes', 3), 'image': img(a.get('image')), 'html': markdown(a.get('body', '')), 'service': a.get('service', '')}
    acards.append(f'<a class="ac" href="a-{k}.html"><span class="ph"><img src="{esc(arts[k]["image"])}" alt="" loading="lazy"></span><span class="mt"><span>{esc(a.get("label"))}</span><span>{a.get("minutes", 3)} دقائق قراءة</span></span><h3>{esc(a["title"])}</h3><p>{esc(a.get("excerpt"))}</p><span class="rd">اقرأ المقال <span>←</span></span></a>')
hb = hb.replace('{{ARTICLES}}', ''.join(acards))
hb = hb.replace('<div class="sec-head"><div><span class="eyebrow">دليلك الصحي</span>', '<div class="sec-head"><div><span class="eyebrow">دليلك الصحي</span>', 1)
hb = hb.replace('<div class="agrid">', '<div class="agrid">', 1)
hb = hb.replace('<p>مقالات قصيرة وعملية، للأسر اللي ترعى مريض أو كبير في السن.</p></div></div>', '<p>مقالات قصيرة وعملية، للأسر اللي ترعى مريض أو كبير في السن.</p></div><a class="lnk" href="guide.html">كل المقالات ←</a></div>', 1)

assert '{{' not in hb, re.findall(r'\{\{\w+\}\}', hb)
open(OUT + 'home.js', 'w', encoding='utf-8').write(open(T + 'home.js', encoding='utf-8').read().replace('{{ARTICLES_JSON}}', json.dumps(arts, ensure_ascii=False)))
home = (f'<title>أفنان الفائقة · الموقع الثاني</title>\n<meta name="description" content="رعاية طبية منزلية من مركز أفنان الفائقة: أطباء وممرضون وأخصائيون مرخّصون في جميع مناطق المملكة، على مدار الساعة.">\n'
        f'{BOOT}\n{FONTS}\n<link rel="stylesheet" href="s2.css">\n{hb}\n{GSAP}\n<script src="core.js"></script>\n<script src="home.js"></script>\n<script src="stories.js"></script>\n')
open(OUT + 'index.html', 'w', encoding='utf-8').write(home)


# ================================================================ articles, guide, 404, share image, icons
ART_ORDER = order
def acard(k, cls='sc'):
    a = arts[k]; ex = EXC[k]
    return (f'<a class="{cls} rvl" href="a-{k}.html"><span class="ph"><img src="{a["image"]}" alt="" loading="lazy"></span>'
            f'<small>{esc(a["label"])} · {a["minutes"]} دقائق قراءة</small><h3>{esc(a["title"])}</h3><p>{esc(ex)}</p><span class="more">اقرأ المقال <span>←</span></span></a>')
for k in ART_ORDER:
    a = arts[k]; ex = EXC[k]
    rel = [x for x in ART_ORDER if x != k][:3]
    main = f'''<section class="ih" style="padding-bottom:70px" data-ctx="احجز {esc(a['service'])}">
    <div class="wrap ih-grid">
      <div>
        <nav class="crumb rvl" aria-label="مسار الصفحة"><a href="index.html">الرئيسية</a><span>/</span><a href="guide.html">دليلك الصحي</a><span>/</span><span style="opacity:1">{esc(a['label'])}</span></nav>
        <span class="eyebrow rvl">{esc(a['label'])} · {a['minutes']} دقائق قراءة</span>
        <h1 class="rvl d1" style="font-size:clamp(34px,4.4vw,60px)">{esc(a['title'])}</h1>
        <p class="lead rvl d2">{esc(ex)}</p>
      </div>
      <div class="ih-ph rvl-clip rv-clip" style="aspect-ratio:4/3"><img src="{a['image']}" alt=""></div>
    </div>
  </section>
  <section class="blk paper" data-ctx="احجز {esc(a['service'])}">
    <div class="wrap"><article class="legal art-body rvl">{a['html']}
      <div class="art-cta"><div><b>تحتاجون رعاية لهذه الحالة؟</b><span>نرتّب لكم زيارة {esc(a['service'])} في الوقت اللي يناسبكم.</span></div><button class="btn mag" type="button" data-book="{esc(a['service'])}" style="border:0;font:inherit;font-weight:600;font-size:16px;cursor:pointer">احجز زيارة <span class="arr" aria-hidden="true">←</span></button></div>
      <p class="art-note">المحتوى للتوعية، ولا يغني عن استشارة الطبيب المختص.</p>
    </article></div>
  </section>
  <section class="blk ivory" data-ctx="اسألونا عن حالتكم">
    <div class="wrap"><div class="head-row"><div><span class="eyebrow rvl">دليلك الصحي</span><h2 class="rvl d1">مقالات قد تهمكم</h2></div><a class="lnk rvl" href="guide.html">كل المقالات ←</a></div>
    <div class="rel">{''.join(acard(x) for x in rel)}</div></div>
  </section>
  {end_cta()}'''
    write_inner(f'a-{k}.html', a['title'], ex, main)

guide_main = f'''<section class="ih" style="padding-bottom:70px" data-ctx="اسألونا عن حالتكم"><div class="wrap">
    <nav class="crumb rvl" aria-label="مسار الصفحة"><a href="index.html">الرئيسية</a><span>/</span><span style="opacity:1">دليلك الصحي</span></nav>
    <span class="eyebrow rvl">دليلك الصحي</span><h1 class="rvl d1">نصائح تساعدك ترعى أحبابك في البيت</h1>
    <p class="lead rvl d2" style="margin:0">مقالات قصيرة وعملية، كتبناها للأسر اللي ترعى مريض أو كبير في السن.</p></div></section>
  <section class="blk ivory" data-ctx="اسألونا عن حالتكم"><div class="wrap"><div class="hub">{''.join(acard(k) for k in ART_ORDER)}</div></div></section>
  {end_cta()}'''
write_inner('guide.html', 'دليلك الصحي', 'مقالات صحية قصيرة من مركز أفنان الفائقة للأسر اللي ترعى مريض أو كبير في السن في البيت.', guide_main)

nf_main = f'''<section class="ih nf" data-ctx="احجز زيارة في دقيقة"><div class="wrap" style="text-align:center;max-width:720px">
    <div class="nf-arch rvl" aria-hidden="true"><b>404</b></div>
    <h1 class="rvl d1">الصفحة اللي تدورون عليها مو موجودة</h1>
    <p class="lead rvl d2" style="margin-inline:auto">يمكن الرابط تغيّر أو انكتب غلط. ارجعوا للرئيسية، أو احجزوا زيارة مباشرة.</p>
    <div class="acts rvl d3" style="justify-content:center"><a class="btn mag" href="index.html">الرئيسية <span class="arr" aria-hidden="true">←</span></a><button class="ghost" type="button" data-book style="background:none;border:0;border-bottom:1px solid rgba(201,162,78,.6);font:inherit;cursor:pointer;color:var(--on-night)">احجز زيارة</button></div>
  </div></section>'''
write_inner('404.html', 'الصفحة غير موجودة', 'الصفحة غير موجودة في موقع أفنان الفائقة.', nf_main)


# ================================================================ site-wide settings, share card, robots, sitemap
SITE_URL = (SET.get('site_url') or '').rstrip('/')
PREVIEW = bool(SET.get('preview_mode'))
WA = re.sub(r'\D', '', str(SET.get('whatsapp') or '966555185244'))
PH = str(SET.get('phone_display') or '+966 55 518 5244')
STAFF = str(SET.get('staff_count') or 150); REG = str(SET.get('regions') or 13)
for f in glob.glob(OUT + '*.html'):
    t = open(f, encoding='utf-8').read()
    title = re.search(r'<title>(.*?)</title>', t).group(1)
    m = re.search(r'<meta name="description" content="(.*?)">', t); desc = m.group(1) if m else ''
    name = os.path.basename(f)
    extra = (f'<link rel="icon" type="image/png" href="img/favicon.png"><link rel="apple-touch-icon" href="img/apple-touch-icon.png">'
             f'<meta name="theme-color" content="#0d1847"><meta property="og:type" content="website"><meta property="og:locale" content="ar_SA">'
             f'<meta property="og:site_name" content="أفنان الفائقة"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">'
             f'<meta property="og:image" content="{SITE_URL}/img/og.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
             f'<meta name="twitter:card" content="summary_large_image">')
    if SITE_URL and name != '404.html':
        extra += f'<link rel="canonical" href="{SITE_URL}/{"" if name == "index.html" else name}"><meta property="og:url" content="{SITE_URL}/{"" if name == "index.html" else name}">'
    if PREVIEW or name == '404.html':
        extra += '<meta name="robots" content="noindex">'
    t = t.replace(BOOT, extra + '\n' + BOOT, 1)
    if name == 'index.html' and not t.lstrip().lower().startswith('<!doctype'):
        t = '<!doctype html>\n<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n' + t.replace('<link rel="stylesheet" href="s2.css">', '<link rel="stylesheet" href="s2.css">\n</head><body>', 1) + '</body></html>\n'
    t = t.replace('+966 55 518 5244', PH).replace('966555185244', WA)
    t = t.replace('+150', '+' + STAFF).replace('150+', STAFF + '+').replace('data-n="150"', f'data-n="{STAFF}"')
    t = t.replace('13 منطقة', REG + ' منطقة').replace('data-n="13"', f'data-n="{REG}"').replace('في 13 منطقة', 'في ' + REG + ' منطقة')
    open(f, 'w', encoding='utf-8').write(t)
for js in ['home.js']:
    p = OUT + js; t = open(p, encoding='utf-8').read().replace('966555185244', WA); open(p, 'w', encoding='utf-8').write(t)
p = OUT + 'core.js'; t = open(p, encoding='utf-8').read().replace('966555185244', WA); open(p, 'w', encoding='utf-8').write(t)
open(OUT + 'robots.txt', 'w').write('User-agent: *\nDisallow: /\n' if PREVIEW else f'User-agent: *\nDisallow: /admin/\n' + (f'Sitemap: {SITE_URL}/sitemap.xml\n' if SITE_URL else ''))
if SITE_URL and not PREVIEW:
    urls = [n for n in sorted(os.listdir(OUT)) if n.endswith('.html') and n != '404.html']
    open(OUT + 'sitemap.xml', 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{SITE_URL}/{"" if n == "index.html" else n}</loc></url>\n' for n in urls) + '</urlset>\n')
print('built', len(glob.glob(OUT + '*.html')), 'pages ·', len(svcs), 'services ·', len(arts), 'articles ·', 'preview' if PREVIEW else 'live')
