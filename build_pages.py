#!/usr/bin/env python3
"""Build Keobiz N2 fiche-pratique pages from JSON export."""
import json, re, html, os, sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).parent
OUT  = ROOT / "output"
OUT.mkdir(exist_ok=True)

# --- Template skeleton (CSS + chrome) -----------------------------------
CSS = """
:root{
  --indigo:#4848E8; --indigo-600:#3840C8; --indigo-700:#3040A0; --indigo-50:#ECF2FA;
  --green:#08A06F; --green-600:#089068;
  --mint-bg:#D6F0E5; --mint-text:#08805A;
  --peach:#FCEEDC;
  --navy:#1B2D5E; --ink:#1F2A44; --muted:#5B6B82;
  --line:#E5EAF0; --soft:#F6F8FB; --white:#FFFFFF;
  --radius:24px; --radius-sm:14px;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff;color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--indigo);text-decoration:underline;text-underline-offset:2px}
a:hover{text-decoration-thickness:2px}
img{max-width:100%}
.nav{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
.nav-inner{max-width:1320px;margin:0 auto;padding:18px 32px;display:flex;align-items:center;gap:36px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo-mark{width:38px;height:38px;background:var(--green);border-radius:9px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:18px;font-family:Georgia,serif;font-style:italic}
.logo-text{display:flex;flex-direction:column;line-height:1}
.logo-text b{color:var(--navy);font-weight:800;font-size:22px;letter-spacing:-0.3px}
.logo-text small{color:#9AA8BB;font-size:9.5px;letter-spacing:0.18em;margin-top:3px}
.nav-menu{display:flex;gap:30px;font-size:14.5px;color:var(--navy);font-weight:600}
.nav-menu a{color:var(--navy);text-decoration:none;display:flex;align-items:center;gap:6px}
.nav-menu a::after{content:"⌄";font-size:12px;color:#9AA8BB;margin-top:-4px}
.nav-menu a.no-arrow::after{content:""}
.nav-right{margin-left:auto;display:flex;align-items:center;gap:14px}
.nav-phone{font-size:14.5px;color:var(--navy);font-weight:600;text-decoration:none}
.btn{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:13px 22px;font-weight:600;font-size:14.5px;cursor:pointer;border:0;transition:.2s;text-decoration:none}
.btn-indigo{background:var(--indigo);color:#fff}
.btn-green{background:var(--green);color:#fff}
.btn-white{background:#fff;color:var(--navy)}
.crumb{max-width:1320px;margin:0 auto;padding:22px 32px 4px;font-size:13.5px;color:var(--muted)}
.crumb a{color:var(--muted);text-decoration:none}
.crumb .sep{margin:0 10px;color:#B5C0D0}
.wrap{max-width:1320px;margin:0 auto;padding:20px 32px 60px;display:grid;grid-template-columns:280px 1fr;gap:48px}
.toc{position:sticky;top:100px;align-self:start}
.toc h4{margin:0 0 16px;font-size:18px;color:var(--navy);font-weight:800}
.toc ul{list-style:none;padding:0;margin:0}
.toc li a{display:block;padding:12px 14px;border-radius:10px;color:var(--ink);text-decoration:none;line-height:1.4;font-size:14px}
.toc li a:hover{background:var(--soft);color:var(--indigo)}
.toc li.active a{background:var(--soft);color:var(--navy);font-weight:600}
.hero{background:var(--indigo-50);border-radius:var(--radius);padding:46px 60px 50px;margin-bottom:36px;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;right:-80px;top:-80px;width:340px;height:340px;border-radius:50%;border:1px solid #D7DFEC;opacity:.6}
.hero .meta-row{display:flex;align-items:center;gap:14px;margin-bottom:22px}
.hero .pill{background:var(--mint-bg);color:var(--mint-text);padding:6px 14px;border-radius:8px;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.hero .time{color:var(--muted);font-size:13px}
.hero h1{margin:0 0 28px;font-size:42px;line-height:1.15;font-weight:800;color:var(--navy);letter-spacing:-0.8px;max-width:780px}
.hero h1 .accent{color:var(--indigo)}
.hero .cta-row{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.hero-arrow{position:absolute;right:60px;top:36px;color:var(--green);font-size:30px;line-height:1;transform:rotate(35deg)}
.intro p{font-size:16.5px;color:var(--ink);margin:0 0 14px}
.retain{background:linear-gradient(135deg,#4A48E8 0%,#3850D0 60%,#3858C8 100%);color:#fff;border-radius:var(--radius);padding:42px 50px 44px;margin:36px 0;position:relative}
.retain-icon{position:absolute;left:36px;top:-26px;width:54px;height:54px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(72,72,232,.25)}
.retain h3{margin:14px 0 22px;font-size:18px;color:#A7D8E8;font-weight:700}
.retain ul{list-style:none;padding:0;margin:0}
.retain li{padding:14px 0 14px 36px;position:relative;border-top:1px solid rgba(255,255,255,.18)}
.retain li:first-child{border-top:0}
.retain li::before{content:"";position:absolute;left:0;top:18px;width:20px;height:20px;border-radius:50%;border:2px solid rgba(255,255,255,.5);background:transparent}
.retain li::after{content:"";position:absolute;left:7px;top:25px;width:6px;height:6px;border-radius:50%;background:#fff}
.retain li strong{display:block;color:#fff;font-weight:700;margin-bottom:4px;font-size:15.5px}
.retain li span{display:block;color:rgba(255,255,255,.78);font-size:14px;line-height:1.55}
.content h2{font-size:28px;margin:48px 0 14px;color:var(--navy);font-weight:800;letter-spacing:-0.4px;scroll-margin-top:100px}
.content h3{font-size:18.5px;margin:28px 0 10px;color:var(--navy);font-weight:700}
.content p{margin:0 0 14px;color:var(--ink);font-size:15.5px}
.content ul,.content ol{padding-left:0;margin:14px 0 18px;list-style:none}
.content > ul > li, .content section > ul > li{position:relative;padding:6px 0 6px 22px;margin-bottom:4px;font-size:15.5px}
.content > ul > li::before, .content section > ul > li::before{content:"";position:absolute;left:0;top:14px;width:8px;height:8px;border-radius:50%;background:var(--green)}
.content > ol{counter-reset:olist}
.content > ol > li{counter-increment:olist;position:relative;padding:6px 0 6px 36px;margin-bottom:8px;font-size:15.5px}
.content > ol > li::before{content:counter(olist,decimal-leading-zero);position:absolute;left:0;top:8px;color:var(--indigo);font-weight:800;font-size:13px}
.content li strong{color:var(--navy)}
.content ul ul li{position:relative;padding:3px 0 3px 18px;font-size:14.5px;color:var(--muted);list-style:none}
.content ul ul li::before{content:"";position:absolute;left:0;top:13px;width:6px;height:1.5px;background:var(--muted)}
.attention,.advice{border-radius:14px;padding:20px 24px;margin:24px 0}
.attention{background:#FFF6E5;border:1px solid #F5D89B}
.attention h4{margin:0 0 6px;color:#7A4E00;font-size:15.5px}
.attention p{margin:0;font-size:14.5px;color:#5C3A00}
.advice{background:var(--indigo-50);border:1px solid #C7D6F0}
.advice h4{margin:0 0 6px;color:var(--navy);font-size:15.5px}
.advice p{margin:0;font-size:14.5px;color:var(--ink)}
.band{background:linear-gradient(95deg,#4A48E8 0%,#08A06F 130%);color:#fff;border-radius:18px;padding:24px 30px;display:flex;align-items:center;justify-content:space-between;gap:24px;margin:30px 0}
.band h4{margin:0;font-size:17px;font-weight:700;max-width:520px;line-height:1.35}
.band .btn-white{padding:14px 24px}
.peach-block{background:var(--peach);border-radius:var(--radius);padding:34px 38px;margin:30px 0;display:grid;grid-template-columns:1.5fr 1fr;gap:30px;align-items:center}
.peach-block h3{margin:0 0 12px;color:var(--navy);font-size:22px;font-weight:800;line-height:1.25}
.peach-block p{margin:0 0 22px;color:var(--muted);font-size:14.5px}
.peach-illu{display:flex;justify-content:center;align-items:center}
.author{background:var(--indigo-50);border-radius:var(--radius);padding:26px 30px;margin:40px 0 30px;display:grid;grid-template-columns:80px 1fr;gap:22px;align-items:center}
.author-avatar{width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,var(--indigo),var(--indigo-600));color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:26px;font-family:Georgia,serif}
.author h5{margin:0 0 6px;font-size:16px;color:var(--navy);font-weight:700}
.author p{margin:0;font-size:14px;color:var(--muted);line-height:1.6}
.step-nav{display:grid;grid-template-columns:1fr 1fr;gap:30px;padding:24px 0;margin:30px 0}
.step-nav .step{font-size:13.5px;color:var(--indigo);font-weight:600}
.step-nav .step small{display:block;color:var(--muted);font-weight:400;font-size:13px;margin-top:4px}
.step-nav .step.next{text-align:right}
.bottom-cta{background:var(--indigo-700);color:#fff;border-radius:18px;padding:26px 32px;display:flex;align-items:center;justify-content:space-between;gap:24px;margin:30px 0 0}
.bottom-cta h3{margin:0;font-size:18px;font-weight:700;max-width:430px;line-height:1.35}
.bottom-cta .btn-white{padding:14px 26px}
.site-footer{background:linear-gradient(180deg,var(--indigo-700) 0%,#283890 100%);color:rgba(255,255,255,.78);padding:60px 32px 30px;margin-top:60px;border-radius:32px 32px 0 0}
.foot-inner{max-width:1320px;margin:0 auto;display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:40px}
.foot-brand .logo-mark{background:#fff;color:var(--green)}
.foot-brand .logo-text b{color:#fff}
.foot-brand .logo-text small{color:rgba(255,255,255,.6)}
.foot-social{display:flex;gap:10px;margin-top:18px}
.foot-social a{width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,.12);color:#fff;display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:13px}
.foot-cert{margin-top:22px;display:inline-flex;align-items:center;gap:8px;background:#F23358;color:#fff;border-radius:8px;padding:8px 12px;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}
.foot-col h6{color:#fff;margin:0 0 14px;font-size:14.5px;font-weight:700}
.foot-col a{display:block;color:rgba(255,255,255,.78);font-size:14px;padding:5px 0;text-decoration:none}
.foot-legal{max-width:1320px;margin:34px auto 0;padding-top:20px;border-top:1px solid rgba(255,255,255,.15);display:flex;justify-content:space-between;font-size:12.5px;color:rgba(255,255,255,.55);gap:20px;flex-wrap:wrap}
.foot-legal a{color:rgba(255,255,255,.7);text-decoration:none}
"""

PHONE_SVG = """<svg viewBox="0 0 200 220" fill="none">
<rect x="40" y="20" width="90" height="170" rx="14" fill="#fff" stroke="#1B2D5E" stroke-width="2"/>
<rect x="50" y="40" width="70" height="8" rx="3" fill="#4848E8"/>
<rect x="50" y="56" width="50" height="6" rx="3" fill="#E5EAF0"/>
<rect x="50" y="70" width="70" height="40" rx="6" fill="#ECF2FA"/>
<rect x="50" y="150" width="70" height="22" rx="6" fill="#08A06F"/>
<rect x="100" y="60" width="80" height="140" rx="12" fill="#fff" stroke="#1B2D5E" stroke-width="2"/>
<rect x="110" y="78" width="60" height="6" rx="3" fill="#4848E8"/>
<rect x="110" y="106" width="60" height="30" rx="5" fill="#ECF2FA"/>
<rect x="110" y="144" width="60" height="18" rx="5" fill="#4848E8"/>
</svg>"""

CHECK_SVG = '<svg viewBox="0 0 24 24" width="26" height="26" fill="none"><path d="M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" stroke="#08A06F" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

NAV_HTML = """<nav class="nav"><div class="nav-inner">
  <a class="logo" href="#"><div class="logo-mark">k</div><div class="logo-text"><b>keobiz</b><small>BY KEROGO FINANCE</small></div></a>
  <div class="nav-menu"><a href="#">Expert comptable</a><a href="#">Création d'entreprise</a><a href="#" class="no-arrow">Tarifs</a><a href="#">Ressources</a></div>
  <div class="nav-right"><a class="nav-phone" href="tel:0176410560">📞 01 76 41 05 60</a><a class="btn btn-indigo" href="#">Obtenir un devis</a><a class="btn btn-green" href="#">Se connecter</a></div>
</div></nav>"""

FOOTER_HTML = """<footer class="site-footer"><div class="foot-inner">
  <div class="foot-brand">
    <a class="logo" href="#"><div class="logo-mark">k</div><div class="logo-text"><b>keobiz</b><small>BY KEROGO FINANCE</small></div></a>
    <div class="foot-social"><a href="#">f</a><a href="#">▶</a><a href="#">◉</a><a href="#">in</a></div>
    <div class="foot-cert">ENTREPRISE LABEL · QUALIANOR</div>
  </div>
  <div class="foot-col"><h6>Nos services</h6><a href="#">Expert comptable en ligne</a><a href="#">Création d'entreprise</a><a href="#">Bilan & liasse fiscale</a><a href="#">Conseil juridique</a></div>
  <div class="foot-col"><h6>Nos ressources</h6><a href="#">Le mag</a><a href="#">Nos outils</a><a href="#">Guides</a><a href="#">Modèles</a></div>
  <div class="foot-col"><h6>À propos de Keobiz</h6><a href="#">Notre cabinet à Paris</a><a href="#">Notre cabinet à Rouen</a><a href="#">Témoignages</a><a href="#">Qui sommes-nous</a><a href="#">Nous contacter</a></div>
</div><div class="foot-legal"><span>© 2026 Keobiz, tous droits réservés.</span><span><a href="#">CGU</a> · <a href="#">Mentions légales</a> · <a href="#">Cookies</a></span></div></footer>"""

# --- Content transformation ---------------------------------------------

FAQ_PATTERNS = re.compile(r"(questions?\s+fr[ée]quent|FAQ|foire\s+aux\s+questions)", re.I)

def strip_faq(soup):
    """Remove the FAQ H2 and everything following it (until next H2 or end)."""
    for h2 in soup.find_all("h2"):
        if FAQ_PATTERNS.search(h2.get_text(" ", strip=True)):
            # remove everything from h2 onward up to next h2 (or end)
            to_remove = [h2]
            sib = h2.find_next_sibling()
            while sib and (sib.name != "h2"):
                to_remove.append(sib)
                sib = sib.find_next_sibling()
            for el in to_remove:
                el.decompose()
            break
    return soup

def split_title(title):
    """Split title to put the last meaningful part in indigo accent."""
    title = title.strip()
    # try to find ' - ' or ' : '
    for sep in [" - ", " : ", " — "]:
        if sep in title:
            base, accent = title.rsplit(sep, 1)
            return base, accent
    words = title.split()
    if len(words) > 4:
        return " ".join(words[:-2]), " ".join(words[-2:])
    return title, ""

def build_retain_items(soup, h2_titles):
    """Generate 'Ce que vous devez retenir' from H2 section intros."""
    items = []
    for h2 in soup.find_all("h2"):
        h2_text = h2.get_text(" ", strip=True)
        # short label = first noun phrase of H2
        label = h2_text.split(":")[0].split("?")[0].strip()
        if len(label) > 60:
            label = label[:57] + "..."
        # description = next paragraph's first sentence
        p = h2.find_next_sibling("p")
        desc = ""
        if p:
            txt = p.get_text(" ", strip=True)
            # first sentence
            m = re.split(r"(?<=[.!?])\s+", txt)
            desc = m[0] if m else txt
            if len(desc) > 180:
                desc = desc[:177] + "..."
        items.append((label, desc))
        if len(items) >= 4:
            break
    return items

def insert_inline_blocks(soup):
    """Insert band CTA + peach block at strategic positions among H2s."""
    h2s = soup.find_all("h2", recursive=False) if False else soup.find_all("h2")
    if not h2s:
        return
    band_html = """<div class="band"><h4>Sécurisez votre projet avec un expert-comptable Keobiz</h4><a class="btn btn-white" href="#">Besoin d'aide pour vous lancer ?</a></div>"""
    peach_html = f"""<div class="peach-block"><div><h3>Marre de l'administratif avant même d'avoir commencé ?</h3><p>Laissez nos experts Keobiz structurer votre projet pendant que vous peaufinez votre activité. Nous gérons la complexité pour vous.</p><a class="btn btn-green" href="#">Créer mon entreprise gratuitement →</a></div><div class="peach-illu">{PHONE_SVG}</div></div>"""

    # band after the 2nd H2 section, peach after the 3rd H2 section
    if len(h2s) >= 3:
        h2s[2].insert_before(BeautifulSoup(band_html, "html.parser"))
    if len(h2s) >= 4:
        h2s[3].insert_before(BeautifulSoup(peach_html, "html.parser"))

def render_page(article, prev_art=None, next_art=None):
    soup = BeautifulSoup(article["content_html"], "html.parser")

    # 1) Remove FAQ entirely (no FAQ in N2 template)
    strip_faq(soup)

    # 2) Remove inline <img> placeholders (no real images in JSON)
    for img in soup.find_all("img"):
        img.decompose()

    # 3) Extract h2s for sommaire + retain block
    h2_list = []
    for i, h2 in enumerate(soup.find_all("h2"), start=1):
        anchor = f"s{i}"
        h2["id"] = anchor
        h2_list.append((anchor, h2.get_text(" ", strip=True)))

    retain_items = build_retain_items(soup, h2_list)

    # 4) Pop the first 2 <p> as intro
    intro_paras = []
    # consume leading nodes until first h2
    while True:
        first = soup.find()
        if not first: break
        if first.name == "h2": break
        if first.name == "p" and len(intro_paras) < 2:
            intro_paras.append(str(first))
            first.decompose()
        else:
            # leave non-p leading content as is (rare)
            break

    # 5) Insert inline CTAs
    insert_inline_blocks(soup)

    # 6) Build pieces
    title = article["title"]
    base, accent = split_title(title)
    h1_html = html.escape(base) + (f' <span class="accent">{html.escape(accent)}</span>' if accent else "")
    metadesc = article.get("metadescription", "")

    sommaire_html = "\n".join(
        '<li{cls}><a href="#{anc}">{txt}</a></li>'.format(
            cls=' class="active"' if i == 0 else '',
            anc=anc,
            txt=html.escape(txt[:70]),
        )
        for i, (anc, txt) in enumerate(h2_list)
    )

    retain_html = "\n".join(
        f'<li><strong>{html.escape(lbl)}</strong><span>{html.escape(desc)}</span></li>'
        for lbl, desc in retain_items
    )

    intro_html = "\n".join(intro_paras)
    content_html = str(soup)

    # word count → reading time
    minutes = max(2, round(article["word_count"] / 230))

    # step nav (prev/next link in batch)
    prev_html = f'<div class="step prev">← Étape précédente<small>{html.escape(prev_art["title"][:60]) if prev_art else "—"}</small></div>'
    next_html = f'<div class="step next">Étape suivante →<small>{html.escape(next_art["title"][:60]) if next_art else "—"}</small></div>'

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(article['metatitle'])}</title>
<meta name="description" content="{html.escape(metadesc)}">
<style>{CSS}</style></head><body>
{NAV_HTML}
<div class="crumb"><a href="#">Accueil</a><span class="sep">/</span><a href="#">Fiches pratiques</a><span class="sep">/</span><span style="color:var(--navy);font-weight:500">{html.escape(base)}</span></div>
<div class="wrap">
  <aside class="toc"><h4>Sommaire</h4><ul>{sommaire_html}</ul></aside>
  <main>
    <section class="hero">
      <span class="hero-arrow">↘</span>
      <div class="meta-row"><span class="pill">Guide complet</span><span class="time">{minutes} min</span></div>
      <h1>{h1_html}</h1>
      <div class="cta-row"><a class="btn btn-indigo" href="#">Être accompagné par un expert →</a></div>
    </section>
    <section class="intro">{intro_html}</section>
    <section class="retain">
      <div class="retain-icon">{CHECK_SVG}</div>
      <h3>Ce que vous devez retenir :</h3>
      <ul>{retain_html}</ul>
    </section>
    <div class="content">
      {content_html}
      <div class="author">
        <div class="author-avatar">MD</div>
        <div><h5>Marcel Delaregardière</h5><p>Expert-comptable chez Keobiz, Marcel accompagne chaque année plus de 200 dirigeants dans la structuration juridique et fiscale de leur projet.</p></div>
      </div>
      <div class="step-nav">{prev_html}{next_html}</div>
      <div class="bottom-cta"><h3>La création d'une entreprise ça ne s'improvise pas, on s'en parle ?</h3><a class="btn btn-white" href="#">Besoin d'aide pour vous lancer ?</a></div>
    </div>
  </main>
</div>
{FOOTER_HTML}
</body></html>"""

# --- Main ---------------------------------------------------------------
def main():
    with open(ROOT / "articles-export-2026-05-19.json") as f:
        articles = json.load(f)
    N = 10
    selection = articles[:N]
    for i, art in enumerate(selection):
        prev_art = selection[i-1] if i > 0 else None
        next_art = selection[i+1] if i < N-1 else None
        slug = art["slug"]
        html_out = render_page(art, prev_art, next_art)
        path = OUT / f"{i+1:02d}-{slug}.html"
        path.write_text(html_out, encoding="utf-8")
        print(f"  ✓ {path.name} ({art['word_count']} mots)")

if __name__ == "__main__":
    main()
