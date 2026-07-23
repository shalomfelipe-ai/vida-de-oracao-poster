#!/usr/bin/env python3
"""
Poster de SANTO DO DIA do @felipebzr_ — peca EXTRA (nao conta como o post nem o
story do dia; a fila evergreen continua igual). Publica cedo (disparado no inicio
da tarefa da manha, antes do poster_stories): um REEL no feed + um STORY.

Regra (Felipe 23/07): santo do dia entra como extra e vai bem cedo no dia.
O feed regular das 12h e o story regular da manha seguem normais — poster_diario
e poster_stories ficam santo-aware e ignoram estas pecas na checagem "ja no ar"
(feed regular so conta a partir das 11h BRT; story regular ignora o id do santo).

Guard proprio: posted_santo.json (chaves 'AAAA-MM-DD-feed' e 'AAAA-MM-DD-story').
Dedup entre PC e nuvem: se ja ha um feed de MANHA no ar (hora < 11 BRT), assume que
o santo ja foi postado por outra maquina e nao republica.
"""
import re, sys, json, datetime, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTA = HERE.parent
sys.path.insert(0, str(HERE))
from postar_instagram_api import (publish_reel, load_secrets, feed_hoje_ids_brt,  # noqa
                                  container_com_fallback, _post)
try:
    from alerta_telegram import alertar_falha as _alerta_falha, alertar_sucesso as _alerta_ok
except Exception:
    def _alerta_falha(*a, **k):
        return False
    def _alerta_ok(*a, **k):
        return False


# data -> dict(feed=[arquivos], feed_lote, feed_secao, story=arquivo|None, story_lote)
CAL_SANTO = {
    "2026-07-26": {
        "feed": ["santa_ana_reel_music.mp4"], "feed_lote": "lote-santo-ana",
        "feed_secao": "Legenda do post",
        "story": "santa_ana_story.png", "story_lote": "lote-santo-ana",
    },
}
CAL_SANTO_DATES = set(CAL_SANTO)

STATE = HERE / "posted_santo.json"


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def registrar(status):
    with open(HERE / "santo_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {status}\n")
    print(f"[{now()}] {status}")


def _load_state(p):
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        try:
            os.replace(p, p.with_suffix(".corrupto.bak"))
        except Exception:
            pass
        return {}


def _save_state(p, d):
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


# ---- helpers lidos por poster_diario / poster_stories (santo-aware) ----
def santo_feed_ids_hoje(hoje):
    """Ids de media do reel do santo de hoje (pra poster_diario desconsiderar)."""
    v = _load_state(STATE).get(f"{hoje}-feed")
    mid = v.get("media_id") if isinstance(v, dict) else None
    return [mid] if mid and mid != "ja-no-ar" else []


def santo_story_id_hoje(hoje):
    """Id do story do santo de hoje (pra poster_stories desconsiderar)."""
    v = _load_state(STATE).get(f"{hoje}-story")
    mid = v.get("media_id") if isinstance(v, dict) else None
    return mid if mid and mid != "ja-no-ar" else None


def extrair_legenda(lote, secao):
    """Le .../instagram/<lote>/LEGENDAS.md e extrai a legenda da secao dada."""
    md = (INSTA / lote / "LEGENDAS.md").read_text(encoding="utf-8")
    i = md.find(secao)
    if i < 0:
        raise RuntimeError(f"secao '{secao}' nao encontrada em {lote}/LEGENDAS.md")
    j = md.find("**Legenda:**", i)
    if j < 0:
        raise RuntimeError(f"'**Legenda:**' nao encontrada apos '{secao}'")
    start = j + len("**Legenda:**")
    ends = [x for x in (md.find("**Stories:**", start), md.find("\n---", start), md.find("\n## ", start)) if x != -1]
    end = min(ends) if ends else len(md)
    bruto = md[start:end].strip()
    limpas = []
    for linha in bruto.split("\n"):
        s = linha.strip()
        if s.startswith(">"):
            continue
        if re.match(r"^\*\*(nota|obs|observacao|observação|interno|lembrete)\b", s, re.I):
            continue
        limpas.append(linha)
    legenda = "\n".join(limpas).strip()
    legenda = re.sub(r"\n{3,}", "\n\n", legenda)
    if not legenda:
        raise RuntimeError(f"legenda vazia apos limpeza em {lote} / {secao}")
    return legenda


def publish_story(ig_id, img_path, secrets):
    token = secrets["ACCESS_TOKEN"]
    cid = container_com_fallback(ig_id, img_path, token, {"media_type": "STORIES"}, secrets)
    return _post(f"{ig_id}/media_publish", {"creation_id": cid}, token).get("id")


def main():
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    if hoje not in CAL_SANTO:
        registrar(f"sem santo do dia para hoje ({hoje}) — nada postado.")
        return
    cfg = CAL_SANTO[hoje]
    state = _load_state(STATE)
    feed_key, story_key = f"{hoje}-feed", f"{hoje}-story"

    try:
        secrets = load_secrets()
        feeds = feed_hoje_ids_brt(secrets["IG_USER_ID"], secrets["ACCESS_TOKEN"], hoje)
    except Exception as e:
        registrar(f"AVISO {hoje}: checagem 'ja no ar' falhou ({repr(e)[:150]}) NAO posto (nao arriscar duplicata).")
        _alerta_falha(f"Santo {hoje} (checagem)", e)
        return
    # Se ja ha feed de MANHA (hora < 11 BRT), o santo ja saiu (PC ou nuvem): nao republica.
    manha_no_ar = any(t.hour < 11 for _mid, t in feeds)

    # ---------- FEED (reel) ----------
    if feed_key in state:
        registrar(f"{feed_key} ja postado antes — pulando feed.")
    elif manha_no_ar:
        state[feed_key] = {"quando": now(), "media_id": "ja-no-ar"}
        _save_state(STATE, state)
        registrar(f"{hoje}: feed do santo ja esta no ar (outra maquina) — nao republico.")
    else:
        imgs = [str(INSTA / cfg["feed_lote"] / n) for n in cfg["feed"]]
        faltando = [p for p in imgs if not Path(p).exists()]
        if faltando:
            registrar(f"ERRO {hoje}: arquivos do feed faltando: {faltando}")
        else:
            try:
                legenda = extrair_legenda(cfg["feed_lote"], cfg["feed_secao"])
                mid = publish_reel(secrets["IG_USER_ID"], imgs[0], legenda, secrets, share_to_feed=True)
                state[feed_key] = {"quando": now(), "media_id": mid}
                _save_state(STATE, state)
                registrar(f"OK {hoje}: reel do santo publicado media_id={mid}")
                _alerta_ok(f"Santo {hoje} (feed)", mid)
            except Exception as e:
                registrar(f"ERRO {hoje} (feed): {repr(e)[:300]}")
                _alerta_falha(f"Santo {hoje} (feed)", e)

    # ---------- STORY ----------
    nome = cfg.get("story")
    if not nome:
        return
    if story_key in state:
        registrar(f"{story_key} ja postado antes — pulando story.")
        return
    if manha_no_ar:
        state[story_key] = {"quando": now(), "media_id": "ja-no-ar"}
        _save_state(STATE, state)
        registrar(f"{hoje}: story do santo ja no ar (outra maquina) — nao republico.")
        return
    img = (INSTA / nome) if "/" in nome else (INSTA / cfg["story_lote"] / nome)
    if not img.exists():
        registrar(f"ERRO {hoje}: story faltando: {img}")
        return
    try:
        mid = publish_story(secrets["IG_USER_ID"], str(img), secrets)
        state[story_key] = {"quando": now(), "media_id": mid}
        _save_state(STATE, state)
        registrar(f"OK {hoje}: story do santo publicado ({nome}) media_id={mid}")
        _alerta_ok(f"Santo {hoje} (story)", mid)
    except Exception as e:
        registrar(f"ERRO {hoje} (story): {repr(e)[:300]}")
        _alerta_falha(f"Santo {hoje} (story)", e)


if __name__ == "__main__":
    main()
