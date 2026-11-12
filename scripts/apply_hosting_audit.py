"""Apply the site audit to a built public directory without reserializing Tilda HTML."""
import argparse
import html
import json
import os
import re
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape as xml_escape

DOMAIN = 'https://svar-experts.ru'
SECTIONS = {
    'generatory-invertornye': ('Инверторные генераторы', 'Инверторный генератор', 'Модели для дома, дачи и выездной работы. Сравните характеристики и комплектацию в карточках.'),
    'generatory-dizelnye': ('Дизельные генераторы', 'Дизельный генератор', 'Дизельные модели для резервного питания. Характеристики, запуск и комплектация указаны в карточках.'),
    'motopompy': ('Мотопомпы', 'Мотопомпа', 'Мотопомпы для перекачки воды. Уточните назначение, производительность и диаметр патрубков в карточке модели.'),
}
META = {
    'index': ('Генераторы YOKOMOTO, мотопомпы и сварочное оборудование | Свар Эксперт', 'Свар Эксперт — генераторы YOKOMOTO, мотопомпы, сварочные аппараты, компрессоры и стабилизаторы. Подбор оборудования по телефону +7 988 788-80-88.'),
    'catalog': ('Каталог генераторов, мотопомп и сварочного оборудования | Свар Эксперт', 'Каталог Свар Эксперт: генераторы, мотопомпы, компрессоры, стабилизаторы и сварочное оборудование. Сравните модели и характеристики, воспользуйтесь фильтрами по бренду и типу.'),
    'service': ('Сервис и ремонт оборудования | Свар Эксперт', 'Информация о сервисе и ремонте оборудования Свар Эксперт. Свяжитесь с магазином, чтобы уточнить порядок обращения.'),
    'sales': ('Акции на оборудование | Свар Эксперт', 'Акции и предложения на генераторы, инструмент и другое оборудование Свар Эксперт.'),
    'privacypolicy': ('Политика конфиденциальности | Свар Эксперт', 'Политика конфиденциальности сайта Свар Эксперт.'),
}
LETTERS = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
                   'a b v g d e e zh z i i k l m n o p r s t u f kh ts ch sh shch _ y _ e iu ia'.split()))
STYLE = '<style>.audit-section{max-width:1160px;margin:32px auto;padding:0 20px;color:#181818;font:17px/1.55 Arial,sans-serif}.audit-section h1,.audit-section h2{line-height:1.2;margin:0 0 16px}.audit-section p{margin:0 0 16px}.audit-section a{color:#1e45a6}.audit-section nav a{display:inline-block;margin:0 18px 8px 0}.audit-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(210px,100%),1fr));gap:16px;list-style:none;padding:0}.audit-grid li{border:1px solid #ddd;border-radius:12px;padding:12px}.audit-grid img{display:block;width:100%;height:180px;object-fit:contain;background:#fff;margin:0 0 10px}.audit-heading{margin:0;font-weight:inherit;font-size:inherit}</style>'
FIXES = {'Your Name': 'Ваше имя', 'Your Email': 'Электронная почта', 'Your Phone': 'Телефон',
         'Checkout': 'Оформить заказ', 'оборудовование': 'оборудование', 'Оборудовование': 'Оборудование',
         'Акиця': 'Акция', 'В корзинуе': 'В корзину', 'Масленный': 'Масляный', 'Стаблизатор': 'Стабилизатор',
         'Конфедициальность': 'Конфиденциальность'}


def clean(value):
    return ' '.join(html.unescape(re.sub(r'<[^>]*>', ' ', value or '')).split())


def attr(value):
    return html.escape(value, quote=True)


def metadata(source, route, title, description):
    tags = [
        '<title>' + attr(title) + '</title>',
        '<meta name="description" content="' + attr(description) + '">',
        '<meta property="og:title" content="' + attr(title) + '">',
        '<meta property="og:description" content="' + attr(description) + '">',
        '<meta property="og:url" content="' + DOMAIN + route + '">',
        '<link rel="canonical" href="' + DOMAIN + route + '">',
    ]
    source = re.sub(r'<title>.*?</title>|<meta\s+(?:name="description"|property="og:(?:title|description|url)")[^>]*>|<link\s+rel="canonical"[^>]*>', '', source, flags=re.S)
    source = re.sub(r'(<meta\s+property="og:image"\s+content=")(/assets/)', r'\g<1>' + DOMAIN + r'\2', source)
    return source.replace('</head>', '\n'.join(tags) + '\n</head>', 1)


def schema(value):
    return '<script type="application/ld+json">' + json.dumps(value, ensure_ascii=False).replace('<', '\\u003c') + '</script>'


def breadcrumbs(items):
    return schema({'@context': 'https://schema.org', '@type': 'BreadcrumbList',
                   'itemListElement': [{'@type': 'ListItem', 'position': index, 'name': label, 'item': DOMAIN + route}
                                       for index, (label, route) in enumerate(items, 1)]})


def picture(root, product, item, index):
    original = item.get('img', '')
    if not original.startswith('/assets/') or not (root / original.lstrip('/')).is_file():
        return original
    stem = ''.join(LETTERS.get(ch, ch) for ch in unicodedata.normalize('NFC', product['title'].lower()))
    stem = re.sub(r'[^a-z0-9]+', '-', stem).strip('-')[:92].strip('-') or 'oborudovanie'
    destination = '/assets/' + stem + '-' + str(product['uid']) + '-' + str(index) + Path(original).suffix
    target = root / destination.lstrip('/')
    if not target.exists():
        os.link(root / original.lstrip('/'), target)
    return destination


def heading(source, tag, label):
    # Match only the selected text atom, never cross the preceding markup.
    pattern = r"<div (class='tn-atom'[^>]*)>((?:<a [^>]*>)?(?:<strong>)?" + re.escape(label) + r"(?:</strong>)?(?:</a>)?)</div>"
    return re.sub(pattern, lambda m: '<' + tag + ' ' + m[1].replace("class='tn-atom'", "class='tn-atom audit-heading'") + '>' + m[2] + '</' + tag + '>', source, count=1)


def pages(root):
    catalog_path = root / 'catalog-data.json'
    snapshot = json.loads(catalog_path.read_text(encoding='utf-8'))
    products = {urlsplit(p['url']).path: p for p in snapshot['products']}
    photos = {}
    for route, product in products.items():
        gallery = json.loads(product['gallery'] or '[]')
        for index, item in enumerate(gallery, 1):
            item['img'] = picture(root, product, item, index)
            item['alt'] = clean(item.get('alt')) or product['title'] + (f' — фото {index}' if index > 1 else '')
        photos[route] = gallery
        product['gallery'] = json.dumps(gallery, ensure_ascii=False)
    catalog_path.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

    section_links = ''.join(f'<a href="/catalog/{slug}">{data[0]}</a>' for slug, data in SECTIONS.items())
    catalog_links = '<nav aria-label="Разделы каталога">' + section_links + '</nav>'
    company_links = '<nav aria-label="Информация о магазине"><a href="/delivery">Доставка и оплата</a><a href="/service">Сервис и гарантия</a><a href="/about">О компании</a></nav>'
    footer = '<div class="audit-section audit-company-links">' + company_links + '</div>'
    site_paths = []
    product_paths = []
    for path in sorted(root.rglob('*.html')):
        relative = path.relative_to(root).as_posix()
        if relative == 'catalog/index.html':
            continue
        route = '/' if relative == 'index.html' else '/' + relative[:-5]
        source = path.read_text(encoding='utf-8')
        for old, new in FIXES.items():
            source = source.replace(old, new)
        source = re.sub(r'<li class="t-sociallinks__item[^"]*">\s*<a href="[123]"[^>]*>.*?</a></li>(?:&nbsp;)?', '', source, flags=re.S)
        source = source.replace('href="/"><span class="t-btnflex__text">Button</span>', 'href="/catalog"><span class="t-btnflex__text">В каталог</span>')
        product = products.get(route)
        old_title = re.search(r'<title>(.*?)</title>', source, re.S)
        title = clean(old_title[1]) if old_title else ''
        old_desc = re.search(r'<meta name="description" content="([^"]*)"', source)
        description = clean(old_desc[1]) if old_desc else ''
        if product:
            title = product['title']
            description = clean(product.get('descr')) or clean(product.get('text'))
            description = description[:190].rsplit(' ', 1)[0] + '…' if len(description) > 190 else description
            description = description or f'{title}. Характеристики и фотографии в каталоге Свар Эксперт.'
            gallery = photos[route]
            embedded = re.search(r'(\bvar product\s*=\s*)(\{[^\r\n]*\})(?=;)', source)
            if embedded:
                record = json.loads(embedded[2])
                record['gallery'] = product['gallery']
                encoded = json.dumps(record, ensure_ascii=False).replace('</', '<\\/')
                source = source[:embedded.start(2)] + encoded + source[embedded.end(2):]
            if gallery:
                hero = gallery[0]
                source = re.sub(r'(<meta\s+property="og:image"\s+content=")[^"]*', lambda m: m[1] + attr(hero['img']), source, count=1)
                source = re.sub(r'(<meta\s+itemprop="image"\s+content=")[^"]*', lambda m: m[1] + attr(hero['img']), source, count=1)
                fallback = f'<noscript><img src="{attr(hero["img"])}" alt="{attr(hero["alt"])}" style="max-width:100%;height:auto"></noscript>'
                source = re.sub(r'(<div class="t-store__prod-popup__slider[^>]*>)', lambda m: m[1] + fallback, source, count=1)
            category = next(((slug, data[0]) for slug, data in SECTIONS.items() if data[1] == product.get('equipment_type')), None)
            trail = [('Главная', '/'), ('Каталог', '/catalog')]
            if category:
                trail.append((category[1], '/catalog/' + category[0]))
            source = source.replace('</head>', breadcrumbs(trail + [(title, route)]) + '</head>', 1)
        elif route in ('/', '/catalog') or '/' not in relative:
            title, description = META.get(relative[:-5], (title, description or f'{title}. Информация на сайте Свар Эксперт.'))
            source = source.replace('</head>', STYLE + '</head>', 1)
            source = source.replace('</body>', footer + '</body>', 1)
        else:
            description = description or f'{title}. Карточка оборудования Свар Эксперт.'
        if route == '/':
            source = heading(source, 'h1', 'Генераторы YOKOMOTO')
            def linked_photo(match):
                opening, route, original = match.groups()
                product = products.get(route)
                if not product:
                    return match[0]
                image = f'<img src="{attr(original)}" alt="{attr(product["title"])}" loading="lazy" decoding="async" style="display:block;width:100%;height:100%;object-fit:cover;border-radius:inherit">'
                return opening + image + '</a>'
            source = re.sub(r"""(<a class='tn-atom t-bgimg' href="(/catalog/tproduct/[^"]+)" data-original="([^"]+)"[^>]*>)\s*</a>""", linked_photo, source)
            for label in ('Каталог товаров', 'Для бизнеса и строительства', 'Для дома и дачи', 'Рекомендуем новинки'):
                source = heading(source, 'h2', label)
            org = {'@context': 'https://schema.org', '@type': 'Organization', 'name': 'Свар Эксперт',
                   'url': DOMAIN, 'telephone': '+79887888088'}
            source = source.replace('</head>', schema(org) + '</head>', 1)
        elif route == '/catalog':
            content = '<section class="audit-section"><h1>Каталог оборудования</h1><h2>Разделы каталога</h2>' + catalog_links + '</section>'
            source = re.sub(r'(<div class="t-store js-store"[^>]*>)', lambda m: content + m[1], source, count=1)
            source = source.replace('</head>', breadcrumbs([('Главная', '/'), ('Каталог', route)]) + '</head>', 1)
        if route == '/service':
            source = source.replace('</body>', '<section class="audit-section"><h2>Гарантийное обслуживание</h2><p>По вопросам гарантии свяжитесь с магазином и сообщите модель и дату покупки. Условия обслуживания уточняются по документам на товар.</p></section></body>', 1)
        source = metadata(source, route, title, description)
        temporary = path.with_suffix('.html.tmp')
        temporary.write_text(source, encoding='utf-8')
        temporary.replace(path)
        (product_paths if route.startswith('/catalog/tproduct/') else site_paths).append(route)

    def standalone(route, title, description, content, trail):
        doc = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + STYLE + breadcrumbs(trail) + '</head><body><main class="audit-section"><nav aria-label="Навигация"><a href="/">Свар Эксперт</a><a href="/catalog">Каталог</a></nav><h1>' + attr(title) + '</h1>' + content + '</main><footer class="audit-section">' + company_links + '</footer></body></html>'
        (root / (route.lstrip('/') + '.html')).write_text(metadata(doc, route, title + ' | Свар Эксперт', description), encoding='utf-8')
        site_paths.append(route)

    for slug, (title, kind, intro) in SECTIONS.items():
        route = '/catalog/' + slug
        cards = []
        for product_route, product in products.items():
            if product.get('equipment_type') != kind:
                continue
            gallery = photos[product_route]
            image = ''
            if gallery:
                image = f'<img src="{attr(gallery[0]["img"])}" alt="{attr(gallery[0]["alt"])}" loading="lazy" decoding="async">'
            cards.append(f'<li><a href="{attr(product_route)}">{image}{attr(product["title"])}</a></li>')
        assert cards, route
        standalone(route, title, intro, f'<p>{attr(intro)}</p><h2>Модели в каталоге</h2><ul class="audit-grid">' + ''.join(cards) + '</ul>' + catalog_links,
                   [('Главная', '/'), ('Каталог', '/catalog'), (title, route)])

    standalone('/delivery', 'Доставка и оплата', 'Как уточнить условия доставки, оплаты и возврата оборудования.',
               '<h2>Доставка, оплата и возврат</h2><p>Уточните доступные способы доставки и оплаты, стоимость и сроки при согласовании заказа. По вопросам возврата свяжитесь с магазином и сообщите номер заказа или данные покупки.</p><p><a href="tel:+79894635303">+7 989 463-53-03</a></p>',
               [('Главная', '/'), ('Доставка и оплата', '/delivery')])
    standalone('/about', 'О компании', 'Свар Эксперт — каталог генераторов, сварочного оборудования, мотопомп и инструмента.',
               '<h2>Свар Эксперт</h2><p>В каталоге представлены генераторы, мотопомпы, компрессоры, стабилизаторы и сварочное оборудование. По вопросам подбора модели свяжитесь с магазином.</p><p><a href="tel:+79887888088">+7 988 788-80-88</a></p>',
               [('Главная', '/'), ('О компании', '/about')])

    def sitemap(name, routes):
        body = ''.join(f'<url><loc>{xml_escape(DOMAIN + route)}</loc></url>\n' for route in sorted(set(routes)))
        (root / name).write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '</urlset>\n', encoding='utf-8')

    sitemap('sitemap.xml', site_paths + product_paths)
    sitemap('sitemap-store.xml', product_paths)
    (root / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\nSitemap: {DOMAIN}/sitemap-store.xml\n', encoding='utf-8')
    if (root / 'catalog/index.html').is_file():
        shutil.copyfile(root / 'catalog.html', root / 'catalog/index.html.tmp')
        (root / 'catalog/index.html.tmp').replace(root / 'catalog/index.html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('public', type=Path)
    pages(parser.parse_args().public)
