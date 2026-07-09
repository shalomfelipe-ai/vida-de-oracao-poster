#!/usr/bin/env python3
"""Alertas ao Telegram para a automacao do Instagram (@felipebzr_).
Avisa em falhas (ex.: "API access blocked") E em publicacoes bem-sucedidas.
Le TELEGRAM_TOKEN e TELEGRAM_CHAT_ID de env (GitHub Secrets) ou secrets.json.
Nunca quebra o fluxo: qualquer erro no envio e' engolido. Nunca imprime o token.
"""
import os, json, datetime
from pathlib import Path
try:
    import requests
except Exception:
    requests = None

HERE = Path(__file__).resolve().parent
_STATE = HERE / "alertas_enviados.json"


def _cfg():
    tok = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not (tok and chat):
        p = HERE / "secrets.json"
        if p.exists():
            try:
                s = json.loads(p.read_text(encoding="utf-8"))
                tok = tok or str(s.get("TELEGRAM_TOKEN", "")).strip()
                chat = chat or str(s.get("TELEGRAM_CHAT_ID", "")).strip()
            except Exception:
                pass
    return tok, chat


def _load_state():
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(d):
    try:
        _STATE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def enviar(texto, dedup_chave=None):
    """Envia mensagem ao Telegram. Com dedup_chave, envia no maximo 1x/dia por chave."""
    tok, chat = _cfg()
    if not (tok and chat and requests):
        return False
    chave = None
    if dedup_chave:
        chave = datetime.date.today().isoformat() + ":" + dedup_chave
        d = _load_state()
        if d.get(chave):
            return False
    try:
        r = requests.post(
            "https://api.telegram.org/bot" + tok + "/sendMessage",
            json={"chat_id": chat, "text": texto, "disable_web_page_preview": False},
            timeout=15,
        )
        ok = bool(r.ok)
    except Exception:
        ok = False
    if ok and chave:
        d = _load_state()
        d[chave] = datetime.datetime.now().isoformat(timespec="seconds")
        _save_state(d)
    return ok


def _eh_bloqueio(erro) -> bool:
    s = str(erro).lower()
    if "access blocked" in s:
        return True
    if "oauthexception" in s and "200" in s:
        return True
    return False


def alertar_falha(contexto, erro):
    """Alerta acionavel se for bloqueio da Meta; senao alerta generico. Best-effort."""
    try:
        if _eh_bloqueio(erro):
            txt = (u"\U0001F534 Instagram travou (API access blocked).\n"
                   "Contexto: " + str(contexto) + ".\n"
                   "Reative o app pelo celular: https://developers.facebook.com/apps\n"
                   "Depois e' so aguardar o proximo slot (ou rodar de novo).")
            return enviar(txt, dedup_chave="bloqueio")
        txt = (u"⚠️ Falha na automacao do Instagram (" + str(contexto) + ").\n"
               "Erro: " + str(erro)[:300])
        return enviar(txt, dedup_chave="falha:" + str(contexto))
    except Exception:
        return False


def alertar_sucesso(contexto, media_id=None):
    """Confirma uma publicacao bem-sucedida. 1x/dia por contexto. Best-effort."""
    try:
        txt = u"✅ " + str(contexto) + " publicado no Instagram."
        if media_id:
            txt += "\nmedia_id=" + str(media_id)
        return enviar(txt, dedup_chave="ok:" + str(contexto))
    except Exception:
        return False


if __name__ == "__main__":
    ok = enviar("Teste manual do alerta_telegram.py " + datetime.datetime.now().isoformat(timespec="seconds"))
    print("enviado:", ok)
