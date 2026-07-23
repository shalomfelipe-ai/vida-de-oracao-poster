#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Posta UM reel avulso no feed, na hora (uso manual pelo Felipe).
Uso: python postar_reel_avulso.py <lote> <arquivo.mp4> "<secao no LEGENDAS.md>"
Guarda um marcador pra nao repostar o mesmo reel no mesmo dia.
"""
import sys, json, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
INSTA = HERE.parent
sys.path.insert(0, str(HERE))
from postar_instagram_api import publish_reel, load_secrets  # noqa
from poster_diario import extrair_legenda  # noqa
try:
    from alerta_telegram import alertar_sucesso as _ok, alertar_falha as _fail
except Exception:
    def _ok(*a, **k): return False
    def _fail(*a, **k): return False

def main():
    if len(sys.argv) < 4:
        print("Uso: python postar_reel_avulso.py <lote> <arquivo.mp4> \"<secao>\""); return
    lote, arq, secao = sys.argv[1], sys.argv[2], sys.argv[3]
    video = INSTA / lote / arq
    if not video.exists():
        print("ERRO: video nao encontrado:", video); return
    marker = HERE / "reel_avulso_posted.json"
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    chave = f"{hoje}:{arq}"
    done = json.loads(marker.read_text(encoding="utf-8")) if marker.exists() else {}
    if chave in done:
        print(f"JA POSTADO hoje ({chave}) media_id={done[chave]} - nao reposto."); return
    secrets = load_secrets()
    legenda = extrair_legenda(lote, secao)
    print("Postando reel:", arq)
    mid = publish_reel(secrets["IG_USER_ID"], str(video), legenda, secrets, share_to_feed=True)
    done[chave] = mid
    marker.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK media_id =", mid)
    _ok(f"Reel avulso {arq}", mid)

if __name__ == "__main__":
    main()
