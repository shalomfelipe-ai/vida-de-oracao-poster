#!/usr/bin/env python3
"""
Poster de STORIES do @felipebzr_ via API (media_type=STORIES).
Versao NUVEM (GitHub Actions, BACKUP do PC). Recebe o slot: 'manha' (story1) ou 'tarde' (story2).
Publica o story-imagem do dia. Nossos stories tem a pergunta na arte e a
interacao vem por resposta na DM (a API nao poe figurinha nativa, e nao usamos).

Uso (as tarefas do Windows chamam):
    python poster_stories.py manha
    python poster_stories.py tarde
"""
import sys, json, datetime, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTA = HERE.parent
sys.path.insert(0, str(HERE))
from postar_instagram_api import container_com_fallback, _post, wait_ready, load_secrets, stories_hoje_brt  # noqa

# data -> (story_manha, story_tarde, lote)
CAL_S = {
    "2026-07-01": ("seg06_story1.png", "seg06_story2.png", "lote-06-12-jul"),
    "2026-07-02": ("ter07_story1.png", "ter07_story2.png", "lote-06-12-jul"),
    "2026-07-03": ("qua08_story1.png", "qua08_story2.png", "lote-06-12-jul"),
    "2026-07-04": ("qui09_story1.png", "qui09_story2.png", "lote-06-12-jul"),
    "2026-07-05": (None, "story_teresa_so_deus_basta.png", "lote-frases-santo"),
    "2026-07-18": ("sex10_story1.png", "sex10_story2.png", "lote-06-12-jul"),
    "2026-07-19": (None, "story_jac_sede.png", "lote-frases-santo"),
    "2026-07-20": (None, "story_jac_tusabes.png", "lote-frases-santo"),
    "2026-07-22": (None, "story_jac2_fica_comigo.png", "lote-frases-santo"),
    "2026-07-23": (None, "story_jac2_compaixao.png", "lote-frases-santo"),
    "2026-07-25": (None, "story_jac2_aquem_iremos.png", "lote-frases-santo"),
    "2026-07-26": (None, "story_jac2_corca.png", "lote-frases-santo"),
    "2026-07-28": (None, "story_jac2_arroz.png", "lote-frases-santo"),
    "2026-07-06": ("sab11_story1.png", "sab11_story2.png", "lote-06-12-jul"),
    "2026-07-07": ("dom12_story1.png", "dom12_story2.png", "lote-06-12-jul"),
    "2026-07-08": ("seg13_story1.png", "seg13_story2.png", "lote-13-19-jul"),
    "2026-07-09": ("lote-jaculatorias/jac_01_confio.png", "story_joao_entardecer.png", "lote-frases-santo"),
    "2026-07-10": ("qua15_story1.png", "qua15_story2.png", "lote-13-19-jul"),
    "2026-07-11": ("qui16_story1.png", "qui16_story2.png", "lote-13-19-jul"),
    "2026-07-12": ("lote-jaculatorias/jac_02_meu_tudo.png", "story_teresinha_olhar.png", "lote-frases-santo"),
    "2026-07-15": ("lote-jaculatorias/jac_03_aumentai_fe.png", "story_joao_onde_amor.png", "lote-frases-santo"),
    "2026-07-16": ("ter14_story1.png", "ter14_story2.png", "lote-13-19-jul"),
    "2026-07-17": ("sex17_story1.png", "sex17_story2.png", "lote-13-19-jul"),
    "2026-07-13": ("sab18_story1.png", "sab18_story2.png", "lote-13-19-jul"),
    "2026-07-14": ("dom19_story1.png", "dom19_story2.png", "lote-13-19-jul"),    # --- Serie "Jaculatoria de hoje" (stories, jul) ---
    "2026-07-21": ("jac_04_que_eu_veja.png", "jac_05_abba.png", "lote-jaculatorias"),
    "2026-07-24": ("jac_06_meu_senhor.png", "jac_07_espirito.png", "lote-jaculatorias"),
    "2026-07-27": ("jac_08_vossa_vontade.png", "jac_09_mae.png", "lote-jaculatorias"),
    "2026-07-29": ("jac_10_sao_jose.png", None, "lote-jaculatorias"),
    "2026-07-30": ("jac_11_misericordia.png", None, "lote-jaculatorias"),
    "2026-07-31": ("jac_12_tudo_bem.png", None, "lote-jaculatorias"),
}


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def registrar(status):
    with open(HERE / "stories_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {status}\n")
    print(f"[{now()}] {status}")



def _load_state(p):
    """Le o json de estado; se estiver corrompido (ex.: PC desligou no meio da
    gravacao), guarda um backup .corrupto.bak e recomeca vazio em vez de travar."""
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
    """Gravacao atomica: escreve num .tmp e troca, pra nunca truncar o arquivo."""
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def ja_postado(chave):
    return chave in _load_state(HERE / "stories_posted.json")


def marcar(chave, media_id):
    p = HERE / "stories_posted.json"
    d = _load_state(p)
    d[chave] = {"quando": now(), "media_id": media_id}
    _save_state(p, d)


def publish_story(ig_id, img_path, secrets):
    token = secrets["ACCESS_TOKEN"]
    cid = container_com_fallback(ig_id, img_path, token,
                                 {"media_type": "STORIES"}, secrets)
    return _post(f"{ig_id}/media_publish", {"creation_id": cid}, token).get("id")


def main():
    slot = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if slot not in ("manha", "tarde"):
        registrar("ERRO: informe o slot 'manha' ou 'tarde'.")
        return
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    if hoje not in CAL_S:
        registrar(f"sem story para hoje ({hoje}) — nada postado.")
        return
    s1, s2, lote = CAL_S[hoje]
    nome = s1 if slot == "manha" else s2
    if not nome:
        registrar(f"{hoje}-{slot}: sem story neste slot — nada postado.")
        return
    chave = f"{hoje}-{slot}"
    if ja_postado(chave):
        registrar(f"{chave} ja foi postado — pulando.")
        return
    # BACKUP NA NUVEM: se ja ha story do slot no ar hoje, nao duplica.
    # manha = qualquer story de hoje antes das 14h BRT; tarde = das 14h em diante.
    try:
        secrets = load_secrets()
        de_hoje = [t for t in stories_hoje_brt(secrets["IG_USER_ID"], secrets["ACCESS_TOKEN"])
                   if t.strftime("%Y-%m-%d") == hoje]
        ja = any(t.hour < 14 for t in de_hoje) if slot == "manha" else any(t.hour >= 14 for t in de_hoje)
        if ja:
            marcar(chave, "ja-no-ar (PC ou manual)")
            registrar(f"{chave}: story do slot ja esta no ar backup nao precisou agir.")
            return
    except Exception as e:
        registrar(f"AVISO {chave}: checagem 'ja no ar' falhou ({repr(e)[:150]}) NAO posto para nao arriscar duplicata.")
        return
    img = (INSTA / nome) if "/" in nome else (INSTA / lote / nome)
    if not img.exists():
        registrar(f"ERRO {chave}: imagem faltando: {img}")
        return
    try:
        mid = publish_story(secrets["IG_USER_ID"], str(img), secrets)
        marcar(chave, mid)
        registrar(f"OK {chave}: story publicado ({nome}) media_id={mid}")
    except Exception as e:
        registrar(f"ERRO {chave}: {repr(e)[:300]}")


if __name__ == "__main__":
    main()
