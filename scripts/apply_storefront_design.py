"""Apply the shared storefront design to an audited site build."""
import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(sys.argv[1])
CSS = Path(__file__).resolve().parents[1] / 'hosting/reg-ru/site-design.css'
snapshot = json.loads((ROOT / 'catalog-data.json').read_text(encoding='utf-8'))
products = snapshot['products']
by_uid = {str(p['uid']): p for p in products}
NAV = [('/catalog', 'Каталог'), ('/sales', 'Акции'), ('/service', 'Сервис'), ('/forbusiness', 'Для бизнеса')]
LOGO = '<a class="sx-logo" href="/" aria-label="Свар Эксперт, главная"><img src="/site-logo.png" width="846" height="240" alt="Svar Expert YOKOMOTO"></a>'
PHONE = '<a class="sx-phone" href="tel:+79887888088">+7 988 788-80-88</a>'
HOME_REPLACED = {'1893733101', '1694804531', '1620311391'}
RECORD = re.compile(r'<div\b[^>]*\bid="rec\d+"[^>]*\bdata-record-type="\d+"[^>]*>')


def e(value):
    return html.escape(str(value), quote=True)


def image(product, alt=None):
    gallery = json.loads(product['gallery'] or '[]')
    if not gallery:
        return ''
    return f'<img src="{e(gallery[0]["img"])}" alt="{e(product["title"] if alt is None else alt)}" loading="lazy" decoding="async">'


def header(route):
    links = []
    for href, label in NAV:
        state = ' aria-current="page"' if route == href else ''
        links.append(f'<a href="{href}"{state}>{label}</a>')
    return f'<header class="sx-header"><div class="sx-shell sx-bar">{LOGO}<nav class="sx-nav" aria-label="Основное меню">{"".join(links)}</nav><div class="sx-actions"><a class="sx-search" href="/search">Поиск</a>{PHONE}</div></div></header>'


FOOTER = f'''<footer class="sx-footer"><div class="sx-shell sx-footer-inner">
<div>{LOGO}{PHONE}</div>
<nav aria-label="Покупателям"><h2>Покупателям</h2><a href="/catalog">Каталог</a><a href="/delivery">Доставка и оплата</a><a href="/service">Сервис и гарантия</a></nav>
<nav aria-label="О магазине"><h2>О магазине</h2><a href="/about">О компании</a><a href="/forb2bsales">Оптовым покупателям</a><a href="/privacypolicy">Политика конфиденциальности</a></nav>
</div></footer>'''

MOBILE_NAV = '''<nav class="sx-mobile-nav" aria-label="Быстрая навигация">
<a href="/"><span aria-hidden="true">⌂</span>Главная</a>
<a href="/catalog"><span aria-hidden="true">▦</span>Каталог</a>
<a class="sx-mobile-contact" href="https://wa.me/79887888088"><span aria-hidden="true">✆</span>WhatsApp</a>
<a href="/#rec1663734931"><span aria-hidden="true">☆</span>Отзывы</a>
<a href="/#rec1892552401"><span aria-hidden="true">✎</span>Заявка</a>
</nav>'''

def common_assets(source):
    source = re.sub(r'href="/site-design[.]css(?:[?][^"]*)?"', 'href="/site-design.css?v=orange-2"', source, count=1)
    source = re.sub(r'<script src="/site-promotions[.]js(?:[?][^"]*)?" defer></script>', '', source)
    source = source.replace('</head>', '<script src="/site-promotions.js?v=orange-2" defer></script></head>', 1)
    source = re.sub(r'<nav class="sx-mobile-nav"[^>]*>.*?</nav>', '', source, flags=re.S)
    source = re.sub(r'<a class="sx-logo"[^>]*>.*?</a>', lambda _: LOGO, source, flags=re.S)
    return source.replace('</body>', MOBILE_NAV + '</body>', 1)


def promotions():
    slides = [
        ('880477745052', 'YOKOMOTO 4000 IX', 'Компактный инверторный генератор'),
        ('544983720072', 'Мотопомпа YOKOMOTO 50CX', 'Для перекачки воды'),
        ('132652608042', 'YOKOMOTO 4000 EB', 'Бензиновый генератор для резервного питания'),
    ]
    cards = []
    buttons = []
    for index, (uid, label, description) in enumerate(slides):
        state = ' hidden' if index else ''
        current = '' if index else ' aria-current="true"'
        product = by_uid[uid]
        copy = f'<div class="sx-promo-text"><strong>{e(label)}</strong><span>{e(description)}</span><span class="sx-promo-buy">Перейти к покупке</span></div>'
        cards.append(f'<a class="sx-promo-card sx-promo-slide" href="{e(product["url"])}"{state}>{copy}{image(product, "")}</a>')
        buttons.append(f'<button type="button" aria-label="{e(label)}"{current}><span aria-hidden="true"></span></button>')
    stabilizers = urlencode({'tfc_storepartuid[1556473581]': 'Стабилизаторы', 'tfc_div': ':::'})
    return f'''<section class="sx-promo" aria-label="Предложения Свар Эксперт">
<a class="sx-promo-card sx-promo-main" href="/yokomotobrend"><img src="/assets/d94b5ba783720ce019d6e630.webp" alt="" fetchpriority="high"><span>Мощность в любой ситуации</span><h1>Генераторы YOKOMOTO</h1></a>
<a class="sx-promo-card sx-promo-stabilizers" href="{e('/catalog?' + stabilizers)}"><img src="/assets/79a8ba589a3ecd2cbbde150a.webp" alt=""><strong>Стабилизаторы</strong><span>Защита от перепадов</span></a>
<a class="sx-promo-card sx-promo-sale" href="/sales"><img src="/assets/15d5fac205ad5cbdc63f278e.webp" alt="Шуруповёрт в подарок — условия акции"></a>
<div class="sx-promo-rotation" role="group" aria-label="Три товара">{"".join(cards)}<div class="sx-promo-controls" hidden>{"".join(buttons)}<button type="button" class="sx-promo-pause" aria-label="Остановить смену товаров">Ⅱ</button></div></div>
</section>'''


def brands():
    names = ('YOKOMOTO', 'VOLTBERRY', 'BONATEK', 'EDON')
    links = []
    for index, brand in enumerate(names):
        query = urlencode({'tfc_brand[1556473581]': brand, 'tfc_div': ':::'})
        state = '' if index == 0 else ' hidden'
        links.append(f'<a class="sx-brand-link" href="{e("/catalog?" + query)}"{state}>{brand} <span aria-hidden="true">→</span></a>')
    return f'<div class="sx-tile sx-brand-tile"><div><strong>Бренды</strong>{"".join(links)}</div><button type="button" class="sx-brand-next" aria-label="Следующий бренд">↻</button></div>'


def home():
    categories = []
    for part in snapshot['parts']:
        label = part['title']
        candidate = next((p for p in products if part['uid'] in json.loads(p.get('partuids') or '[]') and p['gallery'] not in ('', '[]')), None)
        query = urlencode({'tfc_storepartuid[1556473581]': label, 'tfc_div': ':::'})
        categories.append(f'<a class="sx-tile" href="{e("/catalog?" + query)}"><span>{e(label)}</span>{image(candidate, "") if candidate else ""}</a>')
    picks = []
    for uid in ('570929739812', '285459678102', '289129404822', '507181555652'):
        product = by_uid.get(uid)
        if product:
            picks.append(f'<a class="sx-tile" href="{e(product["url"])}">{image(product, "")}<span>{e(product["title"])}</span></a>')
    return f'''<main class="sx-home sx-shell">
<!-- sx-promo-start -->{promotions()}<!-- sx-promo-end -->
<section class="sx-block"><div class="sx-block-head"><h2>Каталог по разделам</h2><a href="/catalog">Все товары →</a></div><div class="sx-grid">{"".join(categories)}{brands()}</div></section>
<section class="sx-block"><div class="sx-block-head"><h2>Топ за свои деньги</h2><div class="sx-picks-controls" hidden><button type="button" aria-label="Предыдущие товары">←</button><button type="button" aria-label="Следующие товары">→</button></div></div><div class="sx-grid sx-picks" tabindex="0" aria-label="Подборка товаров">{"".join(picks)}</div></section>
<section class="sx-block sx-services" aria-label="Помощь и сервис"><a href="/forbusiness">Подбор для бизнеса →</a><a href="/service">Сервис и гарантия →</a><a href="/sales">Акции →</a></section>
</main>'''


def style_legacy(source, route):
    starts = list(RECORD.finditer(source))
    for index in reversed(range(len(starts))):
        match = starts[index]
        markup = match[0]
        block = source[match.end(): starts[index + 1].start() if index + 1 < len(starts) else len(source)]
        uid, kind = re.search(r'id="rec(\d+)"[^>]*data-record-type="(\d+)"', markup).groups()
        style = None
        if kind == '977':
            style = 'sx-original-footer'
        elif kind in ('450', '985') or (kind == '396' and '#menuopen' in block):
            style = 'sx-original-header'
        elif route == '/' and uid in HOME_REPLACED:
            style = 'sx-home-replaced'
        if style:
            markup = re.sub(r'class="([^"]+)"', lambda m: f'class="{m[1]} {style}"', markup, count=1)
            source = source[:match.start()] + markup + source[match.end():]
    if route == '/':
        # The original hero remains available as source markup for its linked assets.
        source = re.sub(r'<h1\b([^>]*\baudit-heading[^>]*)>(.*?)</h1>', r'<div\1>\2</div>', source, flags=re.S)
    return source


def update(path):
    relative = path.relative_to(ROOT).as_posix()
    route = '/' if relative == 'index.html' else '/' + relative[:-5]
    source = path.read_text(encoding='utf-8')
    if 'id="sx-design"' in source:
        if route == '/':
            source, count = re.subn(r'<main class="sx-home sx-shell">.*?</main>', lambda _: home(), source, count=1, flags=re.S)
            assert count == 1, relative
        source = common_assets(source)
        pending = path.with_suffix('.html.sx-tmp')
        pending.write_text(source, encoding='utf-8')
        pending.replace(path)
        return
    source = style_legacy(source, route)
    source = source.replace('</head>', '<link id="sx-design" rel="stylesheet" href="/site-design.css"></head>', 1)
    extras = home() if route == '/' else ''
    if route.startswith('/catalog/tproduct/'):
        extras = '<nav class="sx-shell sx-crumb" aria-label="Хлебные крошки"><a href="/">Главная</a> / <a href="/catalog">Каталог</a> / Товар</nav>'
    source, count = re.subn(r'<body\b[^>]*>', lambda m: m[0] + header(route) + extras, source, count=1, flags=re.I)
    assert count == 1, relative
    if route in ('/delivery', '/about') or (route.startswith('/catalog/') and not route.startswith('/catalog/tproduct/')):
        source = re.sub(r'<footer class="audit-section">.*?</footer>', '', source, flags=re.S)
    source, count = re.subn(r'</body>', FOOTER + '</body>', source, count=1, flags=re.I)
    assert count == 1, relative
    source = common_assets(source)
    pending = path.with_suffix('.html.sx-tmp')
    pending.write_text(source, encoding='utf-8')
    pending.replace(path)


for page in ROOT.rglob('*.html'):
    if page.relative_to(ROOT).as_posix() != 'catalog/index.html':
        update(page)
if (ROOT / 'catalog/index.html').exists():
    pending = ROOT / 'catalog/index.html.sx-tmp'
    shutil.copyfile(ROOT / 'catalog.html', pending)
    pending.replace(ROOT / 'catalog/index.html')
shutil.copyfile(CSS, ROOT / 'site-design.css')
shutil.copyfile(CSS.with_name('site-promotions.js'), ROOT / 'site-promotions.js')

shutil.copyfile(CSS.with_name('site-logo.png'), ROOT / 'site-logo.png')
