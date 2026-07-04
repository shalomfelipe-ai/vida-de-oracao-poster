#!/usr/bin/env python3
"""
Publica um post no Instagram (@felipebzr_) pela API oficial da Meta.
Suporta carrossel (varias imagens) e post unico.

Uso:
    python postar_instagram_api.py --imagens capa.png s2.png s3.png s4.png \
        --legenda-arquivo legenda.txt
    # ou legenda inline:
    python postar_instagram_api.py --imagens foto.png --legenda "Texto..."

Le segredos de secrets.json (ver GUIA-API-INSTAGRAM.md). NUNCA imprime o token.
Fluxo: hospeda imagem -> cria container(es) -> container de carrossel -> media_publish.
Docs: https://developers.facebook.com/docs/instagram-platform/content-publishing/
"""
import argparse, json, os, sys, time, mimetypes, datetime
from pathlib import Path
import requests

# Instagram API com Instagram Login (token IGAA...) usa graph.instagram.com
GRAPH = "https://graph.instagram.com/v21.0"
HERE = Path(__file__).resolve().parent


def load_secrets():
    # Na NUVEM (GitHub Actions) os segredos vem por variavel de ambiente (Secrets).
    env = {k: os.environ.get(k, "").strip() for k in ("IG_USER_ID", "ACCESS_TOKEN")}
    if all(env.values()):
        return env
    p = HERE / "secrets.json"
    if not p.exists():
        sys.exit("ERRO: falta secrets.json (ver GUIA-API-INSTAGRAM.md).")
    s = json.loads(p.read_text(encoding="utf-8"))
    for k in ("IG_USER_ID", "ACCESS_TOKEN"):
        if not s.get(k):
            sys.exit(f"ERRO: secrets.json sem {k}.")
    return s


# ---------- hospedagem (link publico temporario) ----------
def host_catbox(path: Path) -> str:
    """Sobe para catbox.moe (anonimo, sem conta) e retorna URL publica."""
    with open(path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (path.name, f, mimetypes.guess_type(str(path))[0] or "image/jpeg")},
            timeout=120,
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"catbox falhou: {url}")
    return url


def host_github(path: Path, cfg: dict) -> str:
    """Assume que as imagens ja estao num repo publico; monta o raw URL.
    cfg: {"user":.., "repo":.., "branch":"main", "dir":"lote"}"""
    base = f"https://raw.githubusercontent.com/{cfg['user']}/{cfg['repo']}/{cfg.get('branch','main')}"
    sub = cfg.get("dir", "").strip("/")
    return f"{base}/{sub}/{path.name}" if sub else f"{base}/{path.name}"


def host_litterbox(path: Path) -> str:
    """Irmao do catbox (litterbox, arquivo expira em 24h) — outro dominio/CDN."""
    with open(path, "rb") as f:
        r = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "24h"},
            files={"fileToUpload": (path.name, f, mimetypes.guess_type(str(path))[0] or "image/jpeg")},
            timeout=120,
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"litterbox falhou: {url}")
    return url


def host_tmpfiles(path: Path) -> str:
    """tmpfiles.org (anonimo, expira ~1h) — devolve o link direto /dl/."""
    with open(path, "rb") as f:
        r = requests.post("https://tmpfiles.org/api/v1/upload",
                          files={"file": (path.name, f)}, timeout=120)
    r.raise_for_status()
    url = r.json()["data"]["url"]
    return url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)


def host_0x0(path: Path) -> str:
    """0x0.st (anonimo). Exige User-Agent que nao seja python-requests."""
    with open(path, "rb") as f:
        r = requests.post("https://0x0.st", files={"file": (path.name, f)},
                          headers={"User-Agent": "curl/8.5.0"}, timeout=120)
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"0x0 falhou: {url}")
    return url


def make_public(path: Path, secrets: dict) -> str:
    host = secrets.get("HOST", "catbox")
    if host == "github":
        return host_github(path, secrets.get("GITHUB", {}))
    # cadeia de fallback: catbox -> litterbox -> tmpfiles -> 0x0
    # (03/07/2026: catbox passou a responder 412 e derrubou a postagem do dia)
    ultimo = None
    for nome, fn in (("catbox", host_catbox), ("litterbox", host_litterbox),
                     ("tmpfiles", host_tmpfiles), ("0x0", host_0x0)):
        try:
            url = fn(path)
            print(f"  hospedado em {nome}: ok")
            return url
        except Exception as e:
            print(f"  host {nome} falhou: {e}")
            ultimo = e
    raise RuntimeError(f"todos os hosts de imagem falharam (ultimo erro: {ultimo})")




# ---------- checagens "ja esta no ar?" (para o backup da nuvem nao duplicar) ----------
BRT = datetime.timezone(datetime.timedelta(hours=-3))  # Brasil sem horario de verao


def _get(endpoint, params, token):
    r = requests.get(f"{GRAPH}/{endpoint}", params=dict(params, access_token=token), timeout=60)
    if not r.ok:
        raise RuntimeError(f"GET {endpoint} -> {r.status_code}: {r.text}")
    return r.json()


def _ts_brt(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z").astimezone(BRT)


def feed_ja_hoje(ig_id, token, hoje):
    """True se ja existe post de FEED com data (BRT) == hoje ('YYYY-MM-DD')."""
    d = _get(f"{ig_id}/media", {"fields": "id,timestamp", "limit": 10}, token)
    return any(_ts_brt(m["timestamp"]).strftime("%Y-%m-%d") == hoje for m in d.get("data", []))


def stories_hoje_brt(ig_id, token):
    """Horarios (BRT) dos stories AO VIVO publicados hoje nao entra o que ja expirou."""
    d = _get(f"{ig_id}/stories", {"fields": "id,timestamp"}, token)
    return [_ts_brt(m["timestamp"]) for m in d.get("data", [])]


# ---------- Graph API ----------
def _post(endpoint, data, token):
    data = dict(data, access_token=token)
    r = requests.post(f"{GRAPH}/{endpoint}", data=data, timeout=120)
    if not r.ok:
        raise RuntimeError(f"{endpoint} -> {r.status_code}: {r.text}")
    return r.json()


def create_item_container(ig_id, image_url, token, is_carousel_item):
    data = {"image_url": image_url}
    if is_carousel_item:
        data["is_carousel_item"] = "true"
    return _post(f"{ig_id}/media", data, token)["id"]


def wait_ready(container_id, token, tries=20, delay=3):
    """Espera o container ficar FINISHED antes de publicar."""
    for _ in range(tries):
        r = requests.get(f"{GRAPH}/{container_id}",
                         params={"fields": "status_code", "access_token": token}, timeout=60)
        code = r.json().get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise RuntimeError(f"container {container_id} deu ERROR: {r.text}")
        time.sleep(delay)
    raise RuntimeError(f"container {container_id} nao ficou pronto a tempo.")


def publish(ig_id, imagens, legenda, secrets):
    token = secrets["ACCESS_TOKEN"]
    print(f"Hospedando {len(imagens)} imagem(ns)...")
    urls = [make_public(Path(p), secrets) for p in imagens]

    if len(urls) == 1:
        cid = _post(f"{ig_id}/media", {"image_url": urls[0], "caption": legenda}, token)["id"]
        wait_ready(cid, token)
        creation_id = cid
    else:
        children = []
        for u in urls:
            cid = create_item_container(ig_id, u, token, is_carousel_item=True)
            wait_ready(cid, token)
            children.append(cid)
        creation_id = _post(f"{ig_id}/media",
                            {"media_type": "CAROUSEL", "caption": legenda,
                             "children": ",".join(children)}, token)["id"]
        wait_ready(creation_id, token)

    res = _post(f"{ig_id}/media_publish", {"creation_id": creation_id}, token)
    print(f"PUBLICADO. media id: {res.get('id')}")
    return res.get("id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagens", nargs="+", required=True, help="caminhos das imagens, em ordem")
    ap.add_argument("--legenda", default=None)
    ap.add_argument("--legenda-arquivo", default=None)
    a = ap.parse_args()

    legenda = a.legenda or ""
    if a.legenda_arquivo:
        legenda = Path(a.legenda_arquivo).read_text(encoding="utf-8").strip()

    for p in a.imagens:
        if not Path(p).exists():
            sys.exit(f"ERRO: imagem nao encontrada: {p}")

    secrets = load_secrets()
    publish(secrets["IG_USER_ID"], a.imagens, legenda, secrets)


if __name__ == "__main__":
    main()
