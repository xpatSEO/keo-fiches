#!/usr/bin/env python3
"""Convert articles JSON into Keobiz WordPress fiches_pratiques import format.

Outputs:
  output_cms/json/<NN>-<slug>.json   one file per fiche (same shape as
                                       fiches_pratiques_ID_32098_data.json)
  output_cms/keobiz-fiches-import.xml WXR file for bulk WP import
"""
import json, re, html as html_mod, datetime
from pathlib import Path
from bs4 import BeautifulSoup
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).parent
OUT  = ROOT / "output_cms"
OUT_JSON = OUT / "json"
OUT.mkdir(exist_ok=True)
OUT_JSON.mkdir(exist_ok=True)

# ---------------- Hard-coded constants (copied from demo fiche 32098) ----
AUTHOR_OVERRIDE_ID = 23773
RUBRIQUE_PAGE_ID   = 32101
PROMO_IMAGE_IDS    = [32114, 26987, 32114, 26987, 32114, 26987, 32114, 26987]
RUBNAV_ITEMS = [
    ("#", "Fiches Artisan du BTP",            30850),
    ("#", "Fiches Consultant indépendant",    30847),
    ("#", "Fiches Commerce de proximité",     30845),
    ("#", "Fiches VTC et transport de personnes", 30844),
    ("#", "Fiches Hôtellerie et Restauration", 30853),
]

PROMO_DEFAULT_TITLE = "La création d’une entreprise ça ne s’improvise pas, on s’en parle ?"
PROMO_DEFAULT_TEXT  = "Statut juridique, immatriculation, obligations fiscales... Nous prenons en charge toutes vos démarches de A à Z."
PROMO_DEFAULT_BTN   = "Créer mon entreprise gratuitement"
PROMO_DEFAULT_URL   = "#"

CTA_RDV_TEXT = "La création d’une entreprise ça ne s’improvise <br>pas, on s’en parle ?"
CTA_RDV_BTN  = "Prendre un rendez-vous"
CTA_RDV_URL  = "#"

HERO_BADGE    = "GUIDE COMPLET"
HERO_CTA_LBL  = "Être accompagné dans la création"
HERO_CTA_URL  = "https://www.keobiz.fr/"

RUBNAV_TITLE = "Un projet d’entreprise en particulier ? <br>Retrouvez toutes nos autres <span>fiches pratiques :</span>"

FAQ_RE = re.compile(r"(questions?\s+fr[ée]quent|FAQ|foire\s+aux\s+questions)", re.I)
DEMARCHES_RE = re.compile(r"(d[ée]marches?|checklist)", re.I)

# ACF field key constants (mirror the demo file)
FIELD_KEYS = {
    "hero_badge":      "field_fp_hero_badge",
    "hero_title":      "field_fp_hero_title",
    "hero_cta_label":  "field_fp_hero_cta_label",
    "hero_cta_url":    "field_fp_hero_cta_url",
    "retenir_title":   "field_fp_retenir_title",
    "retenir_text":    "field_fp_retenir_text",
    "retenir_items":   "field_fp_retenir_items",
    "parcours_title":  "field_fp_parcours_title",
    "parcours_steps":  "field_fp_parcours_steps",
    "step_badge":      "field_fp_step_badge",
    "step_title":      "field_fp_step_title",
    "step_subtitle":   "field_fp_step_subtitle",
    "step_title_url":  "field_fp_step_title_url",
    "step_body":       "field_fp_step_body",
    "step_resources":  "field_fp_step_resources",
    "res_label":       "field_fp_res_label",
    "res_url":         "field_fp_res_url",
    "step_promo_title":"field_fp_step_promo_title",
    "step_promo_text": "field_fp_step_promo_text",
    "step_promo_btn":  "field_fp_step_promo_btn",
    "step_promo_btn_url": "field_fp_step_promo_btn_url",
    "step_promo_image":   "field_fp_step_promo_image",
    "dem_title":       "field_fp_dem_title",
    "dem_intro":       "field_fp_dem_intro",
    "dem_steps":       "field_fp_dem_steps",
    "dem_step_text":   "field_fp_dem_step_text",
    "auteur_authors_override": "field_fp_auteur_authors_override",
    "cta_rdv_text":    "field_fp_cta_rdv_text",
    "cta_rdv_btn":     "field_fp_cta_rdv_btn",
    "cta_rdv_url":     "field_fp_cta_rdv_url",
    "rubnav_title":    "field_fp_rubnav_title",
    "rubnav_intro":    "field_fp_rubnav_intro",
    "rubnav_items":    "field_fp_rubnav_items",
    "rubnav_item_url": "field_fp_rubnav_item_url",
    "rubnav_item_label": "field_fp_rubnav_item_label",
    "rubnav_item_icon":  "field_fp_rubnav_item_icon",
}

# ---------------- Helpers ------------------------------------------------

def wp_json(obj):
    """Serialize ACF block JSON with WP's HEX_TAG escaping (< > → \\u003c \\u003e)."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

def block(name, data):
    """Emit an ACF Gutenberg self-closing block."""
    cfg = {"name": f"acf/{name}", "data": data, "mode": "edit"}
    return f"<!-- wp:acf/{name} {wp_json(cfg)} /-->"

def paragraph_block(html_inner):
    return f"<!-- wp:paragraph -->\n{html_inner}\n<!-- /wp:paragraph -->"

def split_title_span(title):
    """Wrap last meaningful chunk of a title in <span> for the indigo accent."""
    title = title.strip()
    # remove the trailing "anticipe" word per user note ("retirer la mention 'anticipe'")
    title = re.sub(r"\s+anticipe\.?\s*$", "", title, flags=re.I)
    for sep in [" - ", " : ", " — "]:
        if sep in title:
            base, accent = title.rsplit(sep, 1)
            return f"{base}{sep}<span>{accent}</span>"
    words = title.split()
    if len(words) > 4:
        return " ".join(words[:-2]) + f" <span>{' '.join(words[-2:])}</span>"
    return f"<span>{title}</span>"

def first_sentence(txt, maxlen=200):
    txt = re.sub(r"\s+", " ", txt).strip()
    parts = re.split(r"(?<=[.!?])\s+", txt)
    out = parts[0] if parts else txt
    return (out[:maxlen-3] + "...") if len(out) > maxlen else out

def strip_section(soup, h2_tag):
    """Remove h2 + every sibling up to next h2."""
    sib = h2_tag.find_next_sibling()
    h2_tag.decompose()
    while sib and sib.name != "h2":
        nxt = sib.find_next_sibling()
        sib.decompose()
        sib = nxt

def extract_section_html(soup, h2_tag):
    """Return inner HTML of section (without the H2)."""
    parts = []
    sib = h2_tag.find_next_sibling()
    while sib and sib.name != "h2":
        parts.append(str(sib))
        sib = sib.find_next_sibling()
    return "\n".join(parts).strip()

def safe_html(s):
    """Clean placeholder image tags, normalize whitespace."""
    s = re.sub(r"<img[^>]*/?>", "", s)
    s = re.sub(r"\[image:[^\]]*\]", "", s)
    return s.strip()

# ---------------- ACF block builders -------------------------------------

def hero_data(title_html):
    return {
        "kb_fp_hero_badge": HERO_BADGE,
        "_kb_fp_hero_badge": FIELD_KEYS["hero_badge"],
        "kb_fp_hero_title": title_html,
        "_kb_fp_hero_title": FIELD_KEYS["hero_title"],
        "kb_fp_hero_cta_label": HERO_CTA_LBL,
        "_kb_fp_hero_cta_label": FIELD_KEYS["hero_cta_label"],
        "kb_fp_hero_cta_url": HERO_CTA_URL,
        "_kb_fp_hero_cta_url": FIELD_KEYS["hero_cta_url"],
    }

def retenir_data(title, items):
    d = {
        "kb_fp_retenir_title": title,
        "_kb_fp_retenir_title": FIELD_KEYS["retenir_title"],
    }
    for i, txt in enumerate(items[:4]):
        d[f"kb_fp_retenir_items_{i}_kb_fp_retenir_text"]  = txt
        d[f"_kb_fp_retenir_items_{i}_kb_fp_retenir_text"] = FIELD_KEYS["retenir_text"]
    d["kb_fp_retenir_items"]  = len(items[:4])
    d["_kb_fp_retenir_items"] = FIELD_KEYS["retenir_items"]
    return d

def parcours_data(title_html, steps):
    """steps is a list of dicts: badge, title (with span), subtitle, title_url,
       body (html), resources (list of (label,url) tuples up to 3),
       promo_title, promo_text, promo_btn, promo_btn_url, promo_image_id."""
    d = {
        "kb_fp_parcours_title": title_html,
        "_kb_fp_parcours_title": FIELD_KEYS["parcours_title"],
    }
    for i, st in enumerate(steps[:8]):
        p = f"kb_fp_parcours_steps_{i}_kb_fp_step_"
        d[p+"badge"]    = st["badge"];    d["_"+p+"badge"]    = FIELD_KEYS["step_badge"]
        d[p+"title"]    = st["title"];    d["_"+p+"title"]    = FIELD_KEYS["step_title"]
        d[p+"subtitle"] = st["subtitle"]; d["_"+p+"subtitle"] = FIELD_KEYS["step_subtitle"]
        d[p+"title_url"]= st["title_url"];d["_"+p+"title_url"]= FIELD_KEYS["step_title_url"]
        d[p+"body"]     = st["body"];     d["_"+p+"body"]     = FIELD_KEYS["step_body"]
        for j, (lbl, url) in enumerate(st["resources"][:3]):
            r = f"{p}resources_{j}_kb_fp_res_"
            d[r+"label"] = lbl; d["_"+r+"label"] = FIELD_KEYS["res_label"]
            d[r+"url"]   = url; d["_"+r+"url"]   = FIELD_KEYS["res_url"]
        d[p+"resources"]  = len(st["resources"][:3])
        d["_"+p+"resources"] = FIELD_KEYS["step_resources"]
        d[p+"promo_title"]     = st.get("promo_title", PROMO_DEFAULT_TITLE)
        d["_"+p+"promo_title"] = FIELD_KEYS["step_promo_title"]
        d[p+"promo_text"]      = st.get("promo_text",  PROMO_DEFAULT_TEXT)
        d["_"+p+"promo_text"]  = FIELD_KEYS["step_promo_text"]
        d[p+"promo_btn"]       = st.get("promo_btn",   PROMO_DEFAULT_BTN)
        d["_"+p+"promo_btn"]   = FIELD_KEYS["step_promo_btn"]
        d[p+"promo_btn_url"]   = st.get("promo_btn_url", PROMO_DEFAULT_URL)
        d["_"+p+"promo_btn_url"]= FIELD_KEYS["step_promo_btn_url"]
        d[p+"promo_image"]     = st.get("promo_image_id", PROMO_IMAGE_IDS[i % len(PROMO_IMAGE_IDS)])
        d["_"+p+"promo_image"] = FIELD_KEYS["step_promo_image"]
    d["kb_fp_parcours_steps"]  = len(steps[:8])
    d["_kb_fp_parcours_steps"] = FIELD_KEYS["parcours_steps"]
    return d

def demarches_data(title, intro, steps):
    d = {
        "kb_fp_dem_title": title,  "_kb_fp_dem_title": FIELD_KEYS["dem_title"],
        "kb_fp_dem_intro": intro,  "_kb_fp_dem_intro": FIELD_KEYS["dem_intro"],
    }
    for i, txt in enumerate(steps[:8]):
        d[f"kb_fp_dem_steps_{i}_kb_fp_dem_step_text"]  = txt
        d[f"_kb_fp_dem_steps_{i}_kb_fp_dem_step_text"] = FIELD_KEYS["dem_step_text"]
    d["kb_fp_dem_steps"]  = len(steps[:8])
    d["_kb_fp_dem_steps"] = FIELD_KEYS["dem_steps"]
    return d

def auteur_data():
    return {
        "kb_fp_auteur_authors_override":  AUTHOR_OVERRIDE_ID,
        "_kb_fp_auteur_authors_override": FIELD_KEYS["auteur_authors_override"],
    }

def cta_rdv_data():
    return {
        "kb_fp_cta_rdv_text": CTA_RDV_TEXT,  "_kb_fp_cta_rdv_text": FIELD_KEYS["cta_rdv_text"],
        "kb_fp_cta_rdv_btn":  CTA_RDV_BTN,   "_kb_fp_cta_rdv_btn":  FIELD_KEYS["cta_rdv_btn"],
        "kb_fp_cta_rdv_url":  CTA_RDV_URL,   "_kb_fp_cta_rdv_url":  FIELD_KEYS["cta_rdv_url"],
    }

def rubnav_data():
    d = {
        "kb_fp_rubnav_title": RUBNAV_TITLE, "_kb_fp_rubnav_title": FIELD_KEYS["rubnav_title"],
        "kb_fp_rubnav_intro": "",           "_kb_fp_rubnav_intro": FIELD_KEYS["rubnav_intro"],
    }
    for i, (url, label, icon) in enumerate(RUBNAV_ITEMS):
        p = f"kb_fp_rubnav_items_{i}_kb_fp_rubnav_item_"
        d[p+"url"]   = url;   d["_"+p+"url"]   = FIELD_KEYS["rubnav_item_url"]
        d[p+"label"] = label; d["_"+p+"label"] = FIELD_KEYS["rubnav_item_label"]
        d[p+"icon"]  = icon;  d["_"+p+"icon"]  = FIELD_KEYS["rubnav_item_icon"]
    d["kb_fp_rubnav_items"]  = len(RUBNAV_ITEMS)
    d["_kb_fp_rubnav_items"] = FIELD_KEYS["rubnav_items"]
    return d

# ---------------- Per-article transformer --------------------------------

def build_fiche(article, post_id):
    soup = BeautifulSoup(article["content_html"], "html.parser")

    # Drop placeholder images
    for img in soup.find_all("img"): img.decompose()

    # Strip FAQ section
    for h2 in list(soup.find_all("h2")):
        if FAQ_RE.search(h2.get_text(" ", strip=True)):
            strip_section(soup, h2)
            break

    # Pull leading paragraphs as intro (until first H2)
    intro_paras = []
    for el in list(soup.children):
        if getattr(el, "name", None) == "h2": break
        if getattr(el, "name", None) == "p":
            intro_paras.append(str(el))
            el.decompose()

    # Detect demarches/checklist section (optional, before iterating H2s)
    dem_data = None
    for h2 in list(soup.find_all("h2")):
        if DEMARCHES_RE.search(h2.get_text(" ", strip=True)):
            section_html = extract_section_html(soup, h2)
            sec_soup = BeautifulSoup(section_html, "html.parser")
            intro_p = sec_soup.find("p")
            intro_txt = intro_p.get_text(" ", strip=True) if intro_p else ""
            items = []
            for li in sec_soup.find_all("li"):
                items.append(safe_html(li.decode_contents()))
                if len(items) >= 8: break
            if items:
                dem_data = demarches_data(
                    h2.get_text(" ", strip=True),
                    intro_txt[:300],
                    items,
                )
                strip_section(soup, h2)
            break

    # Remaining H2 sections -> parcours steps
    h2_list = soup.find_all("h2")
    steps = []
    for i, h2 in enumerate(h2_list[:8]):
        h2_text = h2.get_text(" ", strip=True)
        section_html = safe_html(extract_section_html(soup, h2))
        sec_soup = BeautifulSoup(section_html, "html.parser")
        # subtitle = first H3 text or first 80 chars of first paragraph
        subt = ""
        first_h3 = sec_soup.find("h3")
        if first_h3:
            subt = first_h3.get_text(" ", strip=True)
        else:
            first_p = sec_soup.find("p")
            if first_p:
                subt = first_sentence(first_p.get_text(" ", strip=True), 100)
        steps.append({
            "badge": f"Etape {i+1}",
            "title": split_title_span(h2_text),
            "subtitle": subt,
            "title_url": "",
            "body": section_html,
            "resources": [],
        })

    # Retenir items: build from intro of each of the first 4 H2 sections
    retenir_items = []
    for h2 in h2_list[:4]:
        h2_text = re.sub(r"\?$", "", h2.get_text(" ", strip=True)).strip()
        # find first <p> inside section to get a short description
        sib = h2.find_next_sibling()
        desc = ""
        while sib and sib.name != "h2":
            if sib.name == "p":
                desc = first_sentence(sib.get_text(" ", strip=True), 220)
                break
            sib = sib.find_next_sibling()
        if desc:
            retenir_items.append(f"<strong>{h2_text} : </strong>{desc}")
        else:
            retenir_items.append(f"<strong>{h2_text}</strong>")

    # ---- Compose post_content ----
    parts = []
    parts.append(block("fiche-pratique-hero", hero_data(split_title_span(article["title"]))))
    parts.append("")
    for p in intro_paras:
        parts.append(paragraph_block(p))
        parts.append("")
    parts.append(block("fiche-pratique-retenir", retenir_data(
        f"Ce que vous devez retenir : {article['title'].split(' - ')[0].split(' : ')[0]}",
        retenir_items,
    )))
    parts.append("")
    parts.append(block("fiche-pratique-parcours-etapes", parcours_data(
        f"Votre parcours en <span>{len(steps)} étapes</span>",
        steps,
    )))
    parts.append("")
    if dem_data:
        parts.append(block("fiche-pratique-demarches-liste", dem_data))
        parts.append("")
    parts.append(block("fiche-pratique-auteur", auteur_data()))
    parts.append("")
    parts.append(block("fiche-pratique-cta-rendez-vous", cta_rdv_data()))
    parts.append("")
    parts.append(block("fiche-pratique-rubriques-nav", rubnav_data()))

    post_content = "\n".join(parts)

    # ---- Build post_data envelope (mirror demo) ----
    now = datetime.datetime.now(datetime.timezone.utc)
    created = article.get("created_at", now.isoformat()).replace("T", " ").split("+")[0].split(".")[0]
    modified = article.get("updated_at", now.isoformat()).replace("T", " ").split("+")[0].split(".")[0]

    payload = {
        "post_data": {
            "ID": post_id,
            "post_author": "39",
            "post_date": created,
            "post_date_gmt": created,
            "post_content": post_content,
            "post_title": article["title"],
            "post_excerpt": article.get("metadescription", ""),
            "post_status": "publish",
            "comment_status": "closed",
            "ping_status": "closed",
            "post_password": "",
            "post_name": article["slug"],
            "to_ping": "",
            "pinged": "",
            "post_modified": modified,
            "post_modified_gmt": modified,
            "post_content_filtered": "",
            "post_parent": 0,
            "guid": f"http://keobiz.fr/?post_type=fiches_pratiques&p={post_id}",
            "menu_order": 0,
            "post_type": "fiches_pratiques",
            "post_mime_type": "",
            "comment_count": "0",
            "filter": "raw",
        },
        "post_meta": {
            "title": article["title"],
            "_edit_last": "39",
            "_wp_page_template": "default",
            "_wp_old_date": created[:10],
            "_edit_lock": f"{int(now.timestamp())}:39",
            "content-type": "",
            "kb_fp_rubrique_page":  str(RUBRIQUE_PAGE_ID),
            "_kb_fp_rubrique_page": "field_kb_fp_rubrique_page",
            "_custom_header_style": "default",
            "_yoast_wpseo_content_score": "90",
            "_yoast_wpseo_estimated-reading-time-minutes": "",
            "_yoast_wpseo_title": article.get("metatitle", article["title"]),
            "_yoast_wpseo_metadesc": article.get("metadescription", ""),
            "_acf_changed": "1",
        },
        "taxonomies": [],
        "feature_img": False,
        "acf_fields": {"kb_fp_rubrique_page": RUBRIQUE_PAGE_ID},
        "post_type": "fiches_pratiques",
    }
    return payload

# ---------------- WXR (WordPress eXtended RSS) ---------------------------

def wxr_item(payload):
    pd, pm = payload["post_data"], payload["post_meta"]
    meta_xml = "\n".join(
        f"    <wp:postmeta>\n      <wp:meta_key><![CDATA[{k}]]></wp:meta_key>\n      <wp:meta_value><![CDATA[{v}]]></wp:meta_value>\n    </wp:postmeta>"
        for k, v in pm.items()
    )
    return f"""  <item>
    <title>{xml_escape(pd['post_title'])}</title>
    <link>{xml_escape(pd['guid'])}</link>
    <dc:creator><![CDATA[admin]]></dc:creator>
    <guid isPermaLink="false">{xml_escape(pd['guid'])}</guid>
    <description></description>
    <content:encoded><![CDATA[{pd['post_content']}]]></content:encoded>
    <excerpt:encoded><![CDATA[{pd['post_excerpt']}]]></excerpt:encoded>
    <wp:post_id>{pd['ID']}</wp:post_id>
    <wp:post_date><![CDATA[{pd['post_date']}]]></wp:post_date>
    <wp:post_date_gmt><![CDATA[{pd['post_date_gmt']}]]></wp:post_date_gmt>
    <wp:post_modified><![CDATA[{pd['post_modified']}]]></wp:post_modified>
    <wp:post_modified_gmt><![CDATA[{pd['post_modified_gmt']}]]></wp:post_modified_gmt>
    <wp:comment_status><![CDATA[closed]]></wp:comment_status>
    <wp:ping_status><![CDATA[closed]]></wp:ping_status>
    <wp:post_name><![CDATA[{pd['post_name']}]]></wp:post_name>
    <wp:status><![CDATA[publish]]></wp:status>
    <wp:post_parent>0</wp:post_parent>
    <wp:menu_order>0</wp:menu_order>
    <wp:post_type><![CDATA[fiches_pratiques]]></wp:post_type>
    <wp:post_password></wp:post_password>
    <wp:is_sticky>0</wp:is_sticky>
{meta_xml}
  </item>"""

def build_wxr(items):
    body = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:wfw="http://wellformedweb.org/CommentAPI/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
  <title>Keobiz fiches pratiques import</title>
  <link>https://keobiz.fr</link>
  <description>Bulk import of fiches_pratiques</description>
  <pubDate>{datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
  <language>fr-FR</language>
  <wp:wxr_version>1.2</wp:wxr_version>
  <wp:base_site_url>https://keobiz.fr</wp:base_site_url>
  <wp:base_blog_url>https://keobiz.fr</wp:base_blog_url>
  <wp:author>
    <wp:author_id>39</wp:author_id>
    <wp:author_login><![CDATA[admin]]></wp:author_login>
    <wp:author_email><![CDATA[admin@keobiz.fr]]></wp:author_email>
    <wp:author_display_name><![CDATA[Keobiz]]></wp:author_display_name>
  </wp:author>
{body}
</channel>
</rss>
"""

# ---------------- Main ---------------------------------------------------

def main(limit=10):
    with open(ROOT / "articles-export-2026-05-19.json") as f:
        articles = json.load(f)
    selection = articles[:limit]
    items_xml = []
    for i, art in enumerate(selection):
        post_id = 33000 + i  # synthetic IDs starting after demo (32098)
        payload = build_fiche(art, post_id)
        json_path = OUT_JSON / f"{i+1:02d}-{art['slug']}.json"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        items_xml.append(wxr_item(payload))
        print(f"  ✓ {json_path.name}")

    wxr = build_wxr(items_xml)
    wxr_path = OUT / "keobiz-fiches-import.xml"
    wxr_path.write_text(wxr, encoding="utf-8")
    print(f"\n  ✓ {wxr_path.relative_to(ROOT)}  ({len(selection)} fiches)")

if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    main(limit=n)
