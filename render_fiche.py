#!/usr/bin/env python3
"""Render a Keobiz fiches_pratiques JSON payload to a preview HTML page."""
import json, re, html as html_mod, sys
from pathlib import Path

ROOT = Path(__file__).parent

# Reuse the visual identity from build_pages.py
CSS = """
:root{
  --indigo:#4848E8; --indigo-600:#3840C8; --indigo-700:#3040A0; --indigo-50:#ECF2FA;
  --green:#08A06F; --green-600:#089068;
  --mint-bg:#D6F0E5; --mint-text:#08805A;
  --peach:#FCEEDC; --navy:#1B2D5E; --ink:#1F2A44; --muted:#5B6B82;
  --line:#E5EAF0; --soft:#F6F8FB;
  --radius:24px;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff;color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--indigo);text-decoration:underline;text-underline-offset:2px}
img{max-width:100%}
.nav{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
.nav-inner{max-width:1320px;margin:0 auto;padding:18px 32px;display:flex;align-items:center;gap:36px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo-mark{width:38px;height:38px;background:var(--green);border-radius:9px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:18px;font-family:Georgia,serif;font-style:italic}
.logo-text{display:flex;flex-direction:column;line-height:1}
.logo-text b{color:var(--navy);font-weight:800;font-size:22px}
.logo-text small{color:#9AA8BB;font-size:9.5px;letter-spacing:0.18em;margin-top:3px}
.nav-menu{display:flex;gap:30px;font-size:14.5px;color:var(--navy);font-weight:600}
.nav-menu a{color:var(--navy);text-decoration:none}
.nav-right{margin-left:auto;display:flex;align-items:center;gap:14px}
.btn{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:13px 22px;font-weight:600;font-size:14.5px;border:0;text-decoration:none}
.btn-indigo{background:var(--indigo);color:#fff}
.btn-green{background:var(--green);color:#fff}
.btn-white{background:#fff;color:var(--navy)}
.crumb{max-width:1320px;margin:0 auto;padding:22px 32px 4px;font-size:13.5px;color:var(--muted)}
.crumb a{color:var(--muted);text-decoration:none}
.crumb .sep{margin:0 10px;color:#B5C0D0}
.wrap{max-width:1180px;margin:0 auto;padding:20px 32px 60px}
.hero{background:var(--indigo-50);border-radius:var(--radius);padding:46px 60px 50px;margin-bottom:30px;position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;right:-80px;top:-80px;width:340px;height:340px;border-radius:50%;border:1px solid #D7DFEC;opacity:.6}
.hero .pill{display:inline-block;background:var(--mint-bg);color:var(--mint-text);padding:6px 14px;border-radius:8px;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin-bottom:18px}
.hero h1{margin:0 0 28px;font-size:44px;line-height:1.15;font-weight:800;color:var(--navy);letter-spacing:-0.8px;max-width:820px}
.hero h1 span{color:var(--indigo)}
.intro p{font-size:16.5px;color:var(--ink);margin:0 0 14px}
.retain{background:linear-gradient(135deg,#4A48E8 0%,#3850D0 60%,#3858C8 100%);color:#fff;border-radius:var(--radius);padding:42px 50px 44px;margin:30px 0;position:relative}
.retain-icon{position:absolute;left:36px;top:-26px;width:54px;height:54px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(72,72,232,.25)}
.retain h3{margin:14px 0 22px;font-size:18px;color:#A7D8E8;font-weight:700}
.retain ul{list-style:none;padding:0;margin:0}
.retain li{padding:14px 0 14px 36px;position:relative;border-top:1px solid rgba(255,255,255,.18);font-size:14.5px;color:rgba(255,255,255,.85);line-height:1.55}
.retain li:first-child{border-top:0}
.retain li::before{content:"";position:absolute;left:0;top:18px;width:20px;height:20px;border-radius:50%;border:2px solid rgba(255,255,255,.5)}
.retain li::after{content:"";position:absolute;left:7px;top:25px;width:6px;height:6px;border-radius:50%;background:#fff}
.retain li strong{color:#fff;font-weight:700;margin-right:4px}
.parcours-title{font-size:32px;color:var(--navy);font-weight:800;letter-spacing:-0.5px;margin:50px 0 24px;text-align:center}
.parcours-title span{color:var(--indigo)}
.etape{background:#fff;border:1px solid var(--line);border-radius:var(--radius);padding:38px 42px;margin:24px 0;position:relative}
.etape-badge{display:inline-block;background:var(--indigo);color:#fff;padding:6px 16px;border-radius:8px;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin-bottom:14px}
.etape h2{font-size:26px;color:var(--navy);font-weight:800;letter-spacing:-0.3px;margin:0 0 6px;line-height:1.2}
.etape h2 span{color:var(--indigo)}
.etape .subtitle{color:var(--muted);font-size:15px;margin:0 0 22px}
.etape .body{font-size:15.5px;color:var(--ink)}
.etape .body p{margin:0 0 14px}
.etape .body h3{font-size:18px;color:var(--navy);margin:22px 0 10px;font-weight:700}
.etape .body ul,.etape .body ol{padding-left:0;margin:14px 0 18px;list-style:none}
.etape .body ul > li{position:relative;padding:6px 0 6px 22px}
.etape .body ul > li::before{content:"";position:absolute;left:0;top:14px;width:8px;height:8px;border-radius:50%;background:var(--green)}
.etape .body ol{counter-reset:n}
.etape .body ol > li{counter-increment:n;position:relative;padding:6px 0 6px 36px;margin-bottom:8px}
.etape .body ol > li::before{content:counter(n,decimal-leading-zero);position:absolute;left:0;top:8px;color:var(--indigo);font-weight:800;font-size:13px}
.etape .body li strong{color:var(--navy)}
.etape .body ul ul li{position:relative;padding:3px 0 3px 18px;font-size:14.5px;color:var(--muted)}
.etape .body ul ul li::before{content:"";position:absolute;left:0;top:13px;width:6px;height:1.5px;background:var(--muted);border-radius:0}
.etape .body .attention,.etape .body .advice{border-radius:14px;padding:18px 22px;margin:18px 0}
.etape .body .attention{background:#FFF6E5;border:1px solid #F5D89B}
.etape .body .attention h4{margin:0 0 6px;color:#7A4E00;font-size:15px}
.etape .body .attention p{margin:0;font-size:14px;color:#5C3A00}
.etape .body .advice{background:var(--indigo-50);border:1px solid #C7D6F0}
.etape .body .advice h4{margin:0 0 6px;color:var(--navy);font-size:15px}
.etape .body .advice p{margin:0;font-size:14px;color:var(--ink)}
.resources{background:var(--indigo-50);border-radius:14px;padding:18px 22px;margin:24px 0}
.resources-label{font-size:13px;color:var(--navy);font-weight:600;margin-bottom:10px}
.resources-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
.resources-row a{background:#fff;border-radius:10px;padding:12px 14px;font-size:13.5px;color:var(--indigo);display:flex;align-items:flex-start;gap:8px}
.resources-row a::before{content:"→";color:var(--indigo);font-weight:700;flex-shrink:0}
.promo{background:var(--peach);border-radius:18px;padding:28px 32px;margin:30px -8px -8px;display:grid;grid-template-columns:1.4fr 1fr;gap:24px;align-items:center}
.promo h3{margin:0 0 10px;color:var(--navy);font-size:20px;font-weight:800;line-height:1.25}
.promo p{margin:0 0 18px;color:var(--muted);font-size:14.5px}
.promo-illu{display:flex;justify-content:center;align-items:center}
.demarches{background:var(--indigo-50);border-radius:var(--radius);padding:38px 42px;margin:40px 0}
.demarches h2{margin:0 0 10px;color:var(--navy);font-size:24px;font-weight:800}
.demarches .intro{color:var(--muted);font-size:15px;margin-bottom:22px}
.demarches ul{list-style:none;padding:0;margin:0}
.demarches li{padding:12px 0 12px 32px;position:relative;border-top:1px solid #D7DFEC;font-size:14.5px;color:var(--ink)}
.demarches li:first-child{border-top:0}
.demarches li::before{content:"";position:absolute;left:0;top:16px;width:18px;height:18px;border-radius:4px;border:2px solid var(--green)}
.demarches li::after{content:"✓";position:absolute;left:3px;top:11px;color:var(--green);font-weight:800;font-size:14px}
.demarches li strong{color:var(--navy)}
.author{background:var(--indigo-50);border-radius:var(--radius);padding:26px 30px;margin:40px 0 30px;display:grid;grid-template-columns:80px 1fr;gap:22px;align-items:center}
.author-avatar{width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,var(--indigo),var(--indigo-600));color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:26px;font-family:Georgia,serif}
.author h5{margin:0 0 6px;font-size:16px;color:var(--navy);font-weight:700}
.author p{margin:0;font-size:14px;color:var(--muted);line-height:1.6}
.cta-rdv{background:var(--indigo-700);color:#fff;border-radius:18px;padding:26px 32px;display:flex;align-items:center;justify-content:space-between;gap:24px;margin:30px 0}
.cta-rdv h3{margin:0;font-size:18px;font-weight:700;max-width:520px;line-height:1.4}
.rubnav{margin:40px 0 0}
.rubnav h3{font-size:22px;color:var(--navy);font-weight:800;margin:0 0 20px;line-height:1.3}
.rubnav h3 span{color:var(--indigo)}
.rubnav-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.rubnav-item{background:var(--indigo-50);border-radius:14px;padding:18px 20px;display:flex;align-items:center;gap:14px;text-decoration:none;color:var(--navy);font-weight:600;font-size:14.5px}
.rubnav-icon{width:42px;height:42px;border-radius:10px;background:#fff;display:flex;align-items:center;justify-content:center;color:var(--indigo);font-weight:800;font-size:18px;flex-shrink:0}
"""

PHONE_SVG = """<svg viewBox="0 0 200 220" fill="none">
<rect x="40" y="20" width="90" height="170" rx="14" fill="#fff" stroke="#1B2D5E" stroke-width="2"/>
<rect x="50" y="40" width="70" height="8" rx="3" fill="#4848E8"/>
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
  <div class="nav-menu"><a href="#">Expert comptable</a><a href="#">Création d'entreprise</a><a href="#">Tarifs</a><a href="#">Ressources</a></div>
  <div class="nav-right"><a class="btn btn-indigo" href="#">Obtenir un devis</a><a class="btn btn-green" href="#">Se connecter</a></div>
</div></nav>"""

# ---------------- ACF block extractor ----------------------------------
BLOCK_RE = re.compile(r'<!-- wp:acf/(\S+) (\{.*?\}) /-->', re.DOTALL)
PARA_RE  = re.compile(r'<!-- wp:paragraph -->\s*(.*?)\s*<!-- /wp:paragraph -->', re.DOTALL)

def parse_blocks(post_content):
    """Yield (kind, data) tuples in source order."""
    cursor = 0
    # Find positions of all ACF blocks and paragraphs
    events = []
    for m in BLOCK_RE.finditer(post_content):
        events.append((m.start(), m.end(), "acf", m.group(1), m.group(2)))
    for m in PARA_RE.finditer(post_content):
        events.append((m.start(), m.end(), "para", None, m.group(1)))
    events.sort()
    for ev in events:
        if ev[2] == "acf":
            cfg = json.loads(ev[4])
            yield ("acf", ev[3], cfg["data"])
        else:
            yield ("para", None, ev[4])

# ---------------- Block renderers --------------------------------------

def render_hero(d):
    return f"""<section class="hero">
  <span class="pill">{html_mod.escape(d.get('kb_fp_hero_badge',''))}</span>
  <h1>{d.get('kb_fp_hero_title','')}</h1>
  <a class="btn btn-indigo" href="{html_mod.escape(d.get('kb_fp_hero_cta_url','#'))}">{html_mod.escape(d.get('kb_fp_hero_cta_label',''))} →</a>
</section>"""

def render_para(html_inner):
    return f'<section class="intro">{html_inner}</section>'

def render_retenir(d):
    n = d.get("kb_fp_retenir_items", 0)
    items_html = "".join(
        f'<li>{d.get(f"kb_fp_retenir_items_{i}_kb_fp_retenir_text","")}</li>'
        for i in range(n)
    )
    return f"""<section class="retain">
  <div class="retain-icon">{CHECK_SVG}</div>
  <h3>{html_mod.escape(d.get('kb_fp_retenir_title',''))}</h3>
  <ul>{items_html}</ul>
</section>"""

def render_parcours(d):
    n = d.get("kb_fp_parcours_steps", 0)
    title = d.get("kb_fp_parcours_title", "")
    steps_html = []
    for i in range(n):
        p = f"kb_fp_parcours_steps_{i}_kb_fp_step_"
        badge = html_mod.escape(d.get(p+"badge",""))
        st_title = d.get(p+"title","")
        subtitle = html_mod.escape(d.get(p+"subtitle",""))
        body = d.get(p+"body","")
        res_n = d.get(p+"resources",0)
        res_html = ""
        if res_n:
            cells = "".join(
                f'<a href="{html_mod.escape(d.get(f"{p}resources_{j}_kb_fp_res_url","#"))}">{html_mod.escape(d.get(f"{p}resources_{j}_kb_fp_res_label",""))}</a>'
                for j in range(res_n)
            )
            res_html = f'<div class="resources"><div class="resources-label">Vos ressources complémentaires sur ce sujet :</div><div class="resources-row">{cells}</div></div>'
        promo_html = ""
        if d.get(p+"promo_title"):
            promo_html = f"""<div class="promo">
              <div>
                <h3>{html_mod.escape(d.get(p+'promo_title',''))}</h3>
                <p>{html_mod.escape(d.get(p+'promo_text',''))}</p>
                <a class="btn btn-green" href="{html_mod.escape(d.get(p+'promo_btn_url','#'))}">{html_mod.escape(d.get(p+'promo_btn',''))} →</a>
              </div>
              <div class="promo-illu">{PHONE_SVG}</div>
            </div>"""
        steps_html.append(f"""<section class="etape">
          <span class="etape-badge">{badge}</span>
          <h2>{st_title}</h2>
          <p class="subtitle">{subtitle}</p>
          <div class="body">{body}</div>
          {res_html}
          {promo_html}
        </section>""")
    return f'<h2 class="parcours-title">{title}</h2>' + "".join(steps_html)

def render_demarches(d):
    n = d.get("kb_fp_dem_steps", 0)
    items = "".join(
        f'<li>{d.get(f"kb_fp_dem_steps_{i}_kb_fp_dem_step_text","")}</li>'
        for i in range(n)
    )
    return f"""<section class="demarches">
  <h2>{html_mod.escape(d.get('kb_fp_dem_title',''))}</h2>
  <p class="intro">{html_mod.escape(d.get('kb_fp_dem_intro',''))}</p>
  <ul>{items}</ul>
</section>"""

def render_auteur(d):
    # Hard-coded author display (ID 23773 → Marcel)
    return """<section class="author">
  <div class="author-avatar">MD</div>
  <div><h5>Marcel Delaregardière</h5><p>Expert-comptable chez Keobiz, Marcel accompagne chaque année plus de 200 dirigeants dans la structuration juridique et fiscale de leur projet.</p></div>
</section>"""

def render_cta_rdv(d):
    return f"""<section class="cta-rdv">
  <h3>{d.get('kb_fp_cta_rdv_text','')}</h3>
  <a class="btn btn-white" href="{html_mod.escape(d.get('kb_fp_cta_rdv_url','#'))}">{html_mod.escape(d.get('kb_fp_cta_rdv_btn',''))}</a>
</section>"""

def render_rubnav(d):
    n = d.get("kb_fp_rubnav_items", 0)
    items = []
    for i in range(n):
        p = f"kb_fp_rubnav_items_{i}_kb_fp_rubnav_item_"
        label = html_mod.escape(d.get(p+"label",""))
        url   = html_mod.escape(d.get(p+"url","#"))
        # use first letter as fake icon
        initial = (d.get(p+"label","?").replace("Fiches ","")[:1] or "?").upper()
        items.append(f'<a class="rubnav-item" href="{url}"><span class="rubnav-icon">{initial}</span>{label}</a>')
    return f"""<section class="rubnav">
  <h3>{d.get('kb_fp_rubnav_title','')}</h3>
  <div class="rubnav-grid">{"".join(items)}</div>
</section>"""

RENDERERS = {
    "fiche-pratique-hero":           render_hero,
    "fiche-pratique-retenir":        render_retenir,
    "fiche-pratique-parcours-etapes":render_parcours,
    "fiche-pratique-demarches-liste":render_demarches,
    "fiche-pratique-auteur":         render_auteur,
    "fiche-pratique-cta-rendez-vous":render_cta_rdv,
    "fiche-pratique-rubriques-nav":  render_rubnav,
}

# ---------------- Main --------------------------------------------------

def render(json_path: Path, out_path: Path):
    with open(json_path) as f:
        payload = json.load(f)
    if isinstance(payload, list):   # accept [ {...} ] array-wrapped files
        payload = payload[0]
    pd = payload["post_data"]
    body_parts = []
    for kind, name, data in parse_blocks(pd["post_content"]):
        if kind == "para":
            body_parts.append(render_para(data))
        else:
            fn = RENDERERS.get(name)
            if fn:
                body_parts.append(fn(data))
    body = "\n".join(body_parts)
    page = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<title>{html_mod.escape(pd['post_title'])} | Keobiz</title>
<style>{CSS}</style></head><body>
{NAV_HTML}
<div class="crumb"><a href="#">Accueil</a><span class="sep">/</span><a href="#">Fiches pratiques</a><span class="sep">/</span><span style="color:var(--navy)">{html_mod.escape(pd['post_title'])}</span></div>
<main class="wrap">
{body}
</main>
</body></html>"""
    out_path.write_text(page, encoding="utf-8")
    return out_path

if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output_cms/json/01-modele-de-pacte-dassocies.json"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "output_cms/preview_01.html"
    render(src, dst)
    print(f"Rendered: {dst}")
