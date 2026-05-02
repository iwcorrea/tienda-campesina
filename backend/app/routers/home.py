from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Asociacion

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/menu", response_class=HTMLResponse)
def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

# ─── SITEMAP DINÁMICO ────────────────────────────────
@router.get("/sitemap.xml")
def sitemap(db: Session = Depends(get_db)):
    base = "https://tienda-campesina.onrender.com"
    urls = [
        f"{base}/",
        f"{base}/catalogo",
        f"{base}/bolsa-empleo",
        f"{base}/calculadora",
    ]
    # Asociaciones verificadas
    asociaciones = db.query(Asociacion).filter(Asociacion.verificado == "1").all()
    for a in asociaciones:
        urls.append(f"{base}/asociacion/{a.email}")

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        sitemap_xml += f"  <url><loc>{url}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n"
    sitemap_xml += "</urlset>"
    return Response(content=sitemap_xml, media_type="application/xml")

# ─── ROBOTS.TXT ───────────────────────────────────────
@router.get("/robots.txt")
def robots():
    content = """User-agent: *
Allow: /
Disallow: /auth/
Disallow: /admin/
Disallow: /panel/
Sitemap: https://tienda-campesina.onrender.com/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")