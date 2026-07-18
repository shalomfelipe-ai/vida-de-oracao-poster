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
    cfg: {"user":.., "repo":.., "branch":"main", "dir":"lote"}
    18/07/2026: se cfg nao fixa "dir", usa a PASTA DO PROPRIO ARQUIVO
    (ex.: lote-06-12-jul), porque o lote muda a cada dia."""
    base = f"https://raw.githubusercontent.com/{cfg['user']}/{cfg['repo']}/{cfg.get('branch','main')}"
    sub = cfg.get("dir")
    if sub is None:
        sub = Path(path).resolve().parent.name
    sub = str(sub).strip("/")
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


def hosts_chain(secrets=None):
    """Ordem dos hosts. No GitHub Actions o catbox responde 412 e a Meta
    rejeitou URL do litterbox (04/07/2026) -> na nuvem comeca por tmpfiles/0x0.
    18/07/2026: se secrets tem GITHUB, o raw.githubusercontent entra PRIMEIRO
    (os 4 hosts anonimos cairam juntos em 18/07 e derrubaram o feed); os
    anonimos seguem como fallback."""
    padrao = [("tmpfiles", host_tmpfiles), ("0x0", host_0x0),
              ("catbox", host_catbox), ("litterbox", host_litterbox)]
    nuvem = [("tmpfiles", host_tmpfiles), ("0x0", host_0x0),
             ("litterbox", host_litterbox), ("catbox", host_catbox)]
    chain = nuvem if os.environ.get("GITHUB_ACTIONS") else padrao
    cfg = (secrets or {}).get("GITHUB")
    if cfg:
        chain = [("github", lambda p, c=cfg: host_github(Path(p), c))] + chain
    return chain


def make_public(path: Path, secrets: dict) -> str:
    host = secrets.get("HOST", "catbox")
    if host == "github":
        return host_github(path, secrets.get("GITHUB", {}))
    ultimo = None
    for nome, fn in hosts_chain(secrets):
        try:
            url = fn(path)
            print(f"  hospedado em {nome}: ok")
            return url
        except Exception as e:
            print(f"  host {nome} falhou: {e}")
            ultimo = e
    raise RuntimeError(f"todos os hosts de imagem falharam (ultimo erro: {ultimo})")


_ERROS_DE_DOWNLOAD = ("9004", "2207052", "2207003", "36001", "2207083",
                      "Timeout", "timed out", "download",
                      "Only photo or video", "format is not supported",
                      "Unknown Image Format", "could not be processed")


def _erro_de_download(e) -> bool:
    s = str(e)
    return any(k in s for k in _ERROS_DE_DOWNLOAD)


def container_com_fallback(ig_id, path, token, extra=None, secrets=None):
    """Hospeda a imagem e cria o container na Meta; se a Meta nao conseguir
    BAIXAR a midia daquele host (erro de download/timeout), tenta o proximo
    host em vez de desistir. (04/07/2026: Meta rejeitou litterbox na nuvem.)"""
    secrets = secrets or {}
    if secrets.get("HOST") == "github":
        url = host_github(Path(path), secrets.get("GITHUB", {}))
        cid = _post(f"{ig_id}/media", dict(extra or {}, image_url=url), token)["id"]
        wait_ready(cid, token)
        return cid
    ultimo = None
    for nome, fn in hosts_chain(secrets):
        try:
            url = fn(Path(path))
        except Exception as e:
            print(f"  host {nome} falhou no upload: {e}")
            ultimo = e
            continue
        print(f"  hospedado em {nome}: ok")
        try:
            cid = _post(f"{ig_id}/media", dict(extra or {}, image_url=url), token)["id"]
            wait_ready(cid, token)
            return cid
        except Exception as e:
            if _erro_de_download(e):
                print(f"  Meta nao baixou de {nome}; tentando outro host...")
                ultimo = e
                continue
            raise
    raise RuntimeError(f"nenhum host serviu a midia para a Meta (ultimo erro: {ultimo})")


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


def wait_ready(container_id, token, tries=40, delay=3):
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
    if len(imagens) == 1:
        creation_id = container_com_fallback(ig_id, imagens[0], token,
                                             {"caption": legenda}, secrets)
    else:
        children = [container_com_fallback(ig_id, p, token,
                                           {"is_carousel_item": "true"}, secrets)
                    for p in imagens]
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
