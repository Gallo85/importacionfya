# divisas/utils.py
from decimal import Decimal
from django.core.cache import cache
from typing import Any, Iterable
import logging, re, json, requests

logger = logging.getLogger(__name__)

# ---- Config ----
DOLARHOY_BLUE_URL = "https://dolarhoy.com/cotizacion-dolar-blue"
BLUELYTICS_URL    = "https://api.bluelytics.com.ar/v2/latest"

# ⬆️ bump de versión para limpiar cache vieja del servidor
CACHE_KEY_DH = "cotiza:dolarhoy:blue:venta:v7" 
CACHE_KEY_BL = "cotiza:bluelytics:blue:venta:v1"
CACHE_TTL    = 60  # segundos

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# -------------------------------------------------
# Helpers numéricos
# -------------------------------------------------
def _to_decimal(raw: Any) -> Decimal | None:
    try:
        s = str(raw)
        # normaliza "1.445,00" -> "1445.00"
        s = s.replace("\u202f", "").replace(" ", "").replace(".", "").replace(",", ".")
        d = Decimal(s)
        return d if d > 0 else None
    except Exception:
        return None

def _is_plausible_rate(d: Decimal) -> bool:
    # Rango razonable para blue venta
    return Decimal("200") <= d <= Decimal("5000")

def _fix_missed_zero(d: Decimal) -> Decimal | None:
    # Caso típico del scrape: 14450 → 1445
    if Decimal("10000") <= d <= Decimal("50000"):
        d10 = d / Decimal("10")
        if _is_plausible_rate(d10):
            return d10
    return None

def _sanitize_candidate(d: Decimal | None) -> Decimal | None:
    if not d:
        return None
    if _is_plausible_rate(d):
        return d
    return _fix_missed_zero(d)

def _walk(obj: Any, path: list[str]) -> Iterable[tuple[list[str], Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, path + [str(k)])
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, path + [f"[{i}]"])
    else:
        yield (path, obj)

# -------------------------------------------------
# DolarHoy (Next.js + fallback HTML)
# -------------------------------------------------
def _extract_from_next_json(html: str) -> Decimal | None:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.I | re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except Exception as e:
        logger.warning("DolarHoy: NEXT_DATA inválido: %s", e)
        return None

    # Heurística: nodos con contexto blue + venta/sell
    cands: list[Decimal] = []
    for path, value in _walk(data, []):
        if not isinstance(value, (str, int, float)):
            continue
        d = _to_decimal(value)
        if not d:
            continue
        pl = "/".join(p.lower() for p in path)
        if ("blue" in pl or "dolar_blue" in pl) and any(x in pl for x in ("venta", "sell", "ask", "sellprice")):
            cands.append(d)

    if cands:
        mx = _sanitize_candidate(max(cands))
        if mx:
            return mx
    return None

def _extract_from_html(html: str) -> Decimal | None:
    # Ventana alrededor de 'blue'
    m = re.search(r"blue", html, re.I)
    block = html[m.start(): m.start()+8000] if m else html

    # 'Venta' explícito
    m_venta = re.search(
        r"(?i)Venta[^0-9$]{0,160}\$?\s*([0-9]{1,3}(?:[.\u202f\s][0-9]{3})*(?:,[0-9]{1,2})|[0-9]{3,})",
        block, re.S
    )
    if m_venta:
        d = _sanitize_candidate(_to_decimal(m_venta.group(1)))
        if d:
            return d

    # Si falla, tomamos el máximo número del bloque como heurística
    nums = re.findall(r"\$?\s*([0-9]{1,3}(?:[.\u202f\s][0-9]{3})*(?:,[0-9]{1,2})|[0-9]{3,})", block)
    cands = [_sanitize_candidate(_to_decimal(n)) for n in nums]
    cands = [c for c in cands if c]
    if cands:
        mx = max(cands)
        logger.warning("DolarHoy: usando máx del bloque como Venta: %s", mx)
        return mx
    return None

def obtener_dolar_venta_dolarhoy() -> Decimal | None:
    """Solo DolarHoy. Devuelve Decimal o None. Cachea 60s."""
    cached = cache.get(CACHE_KEY_DH)
    if cached is not None:
        d = _sanitize_candidate(_to_decimal(cached))
        if d:
            return d

    try:
        resp = requests.get(
            DOLARHOY_BLUE_URL,
            headers={"User-Agent": UA, "Accept-Language": "es-AR,es;q=0.9"},
            timeout=8,
        )
        resp.raise_for_status()
        html = resp.text

        d = _extract_from_next_json(html) or _extract_from_html(html)
        if d:
            cache.set(CACHE_KEY_DH, str(d), CACHE_TTL)
            return d

        logger.warning("DolarHoy: no se pudo extraer Blue Venta (JSON+HTML).")
        return None
    except requests.RequestException as e:
        logger.error("DolarHoy HTTP error: %s", e)
        return None
    except Exception as e:
        logger.exception("DolarHoy parse error: %s", e)
        return None

# -------------------------------------------------
# Bluelytics (API pública)
# -------------------------------------------------
def obtener_dolar_venta_bluelytics() -> Decimal | None:
    """Bluelytics oficial. Devuelve Decimal o None. Cachea 60s."""
    cached = cache.get(CACHE_KEY_BL)
    if cached is not None:
        d = _sanitize_candidate(_to_decimal(cached))
        if d:
            return d

    try:
        r = requests.get(BLUELYTICS_URL, headers={"User-Agent": UA}, timeout=6)
        r.raise_for_status()
        data = r.json()
        # estructura: {"blue": {"value_sell": 1445.0, ...}, ...}
        blue = data.get("blue") or {}
        val = blue.get("value_sell")
        d = _sanitize_candidate(_to_decimal(val))
        if d:
            cache.set(CACHE_KEY_BL, str(d), CACHE_TTL)
            return d
        return None
    except requests.RequestException as e:
        logger.error("Bluelytics HTTP error: %s", e)
        return None
    except Exception as e:
        logger.exception("Bluelytics parse error: %s", e)
        return None

# -------------------------------------------------
# API pública compatible con tu views.py
# -------------------------------------------------
def obtener_dolar(tipo: str = "blue", campo: str = "venta"):
    """Compatibilidad: usa preferentemente DolarHoy; devuelve Decimal o None (sin inventar)."""
    if tipo != "blue" or campo != "venta":
        logger.warning("obtener_dolar llamado con tipo/campo no soportado: %s/%s", tipo, campo)
    return obtener_dolar_venta_dolarhoy()

def obtener_dolar_venta() -> Decimal | None:
    """Atajo clásico: Blue venta (DolarHoy)."""
    return obtener_dolar("blue", "venta")

# -------------------------------------------------
# Preferencia con backup y chequeo de consistencia
# -------------------------------------------------
def obtener_dolar_venta_prefer(prefer: str = "dolarhoy", backup: str | None = "bluelytics") -> Decimal | None:
    """
    prefer: 'dolarhoy' o 'bluelytics'
    backup: idem o None
    Lógica:
      1) Intentamos proveedor preferido.
      2) Si hay backup y ambos devuelven valor, comparamos:
         - Si difiere > 15%, usamos el backup (p.ej. DolarHoy tomó el Oficial).
      3) Siempre validamos rango/valores plausibles.
    """
    providers = {
        "dolarhoy": obtener_dolar_venta_dolarhoy,
        "bluelytics": obtener_dolar_venta_bluelytics,
    }
    main_fn = providers.get(prefer)
    bkp_fn  = providers.get(backup) if backup else None

    d_main = _sanitize_candidate(main_fn()) if main_fn else None
    if not d_main and bkp_fn:
        return _sanitize_candidate(bkp_fn())

    if d_main and bkp_fn:
        d_bkp = _sanitize_candidate(bkp_fn())
        if d_bkp:
            try:
                diff = abs(d_main - d_bkp) / d_bkp
            except Exception:
                diff = Decimal("1")
            if diff > Decimal("0.15"):
                return d_bkp
    return d_main
