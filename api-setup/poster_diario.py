#!/usr/bin/env python3
"""
Poster DIARIO do feed @felipebzr_ — versao NUVEM (GitHub Actions, BACKUP do PC).
Descobre a data de hoje, acha o post do dia no calendario, le a legenda do
LEGENDAS.md correspondente e publica via API (postar_instagram_api.publish).

Rodar via run_poster.bat (a tarefa do Windows chama esse .bat todo dia).
Nao republica se o dia ja foi postado (guarda em posted.json).
Depois de 14/07 nao ha conteudo aqui (o novo vem do programa de terca).
"""
import json
import re, sys, datetime, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTA = HERE.parent  # .../instagram
sys.path.insert(0, str(HERE))
from postar_instagram_api import publish, load_secrets, feed_ja_hoje  # noqa
try:
    from alerta_telegram import alertar_falha as _alerta_falha, alertar_sucesso as _alerta_ok
except Exception:
    def _alerta_falha(*a, **k):
        return False
    def _alerta_ok(*a, **k):
        return False


# data -> (lista de arquivos de imagem, pasta do lote, rotulo da secao no LEGENDAS.md)
CAL = {
    # ===== EXTRA feeds 29-30/07 (dias que estavam sem feed) =====
    "2026-07-29": (["feed_29.png"], "lote-extra", "EXTRA 29/07"),
    "2026-07-30": (["feed_30.png"], "lote-extra", "EXTRA 30/07"),
    # ===== PONTE 01-03/08 (jaculatorias, bridge p/ agosto) =====
    "2026-08-01": (["p1_post.png"], "lote-ponte-ago", "PONTE 01/08"),
    "2026-08-02": (["p2_post.png"], "lote-ponte-ago", "PONTE 02/08"),
    "2026-08-03": (["p3_post.png"], "lote-ponte-ago", "PONTE 03/08"),
    # ===== AGOSTO (4 semanas tematicas geradas 07/07) =====
    "2026-08-04": (["d1_capa.png", "d1_s2.png", "d1_s3.png", "d1_s4.png"], "lote-ago1-palavra", "SEG 04/08"),
    "2026-08-05": (["d2_post.png"], "lote-ago1-palavra", "TER 05/08"),
    "2026-08-06": (["d3_post.png"], "lote-ago1-palavra", "QUA 06/08"),
    "2026-08-07": (["d4_capa.png", "d4_s2.png", "d4_s3.png", "d4_s4.png"], "lote-ago1-palavra", "QUI 07/08"),
    "2026-08-08": (["d5_post.png"], "lote-ago1-palavra", "SEX 08/08"),
    "2026-08-09": (["d6_post.png"], "lote-ago1-palavra", "SÁB 09/08"),
    "2026-08-10": (["d7_capa.png", "d7_s2.png", "d7_s3.png", "d7_s4.png"], "lote-ago1-palavra", "DOM 10/08"),
    "2026-08-11": (["d1_capa.png", "d1_s2.png", "d1_s3.png", "d1_s4.png"], "lote-ago2-transforma", "SEG 11/08"),
    "2026-08-12": (["d2_post.png"], "lote-ago2-transforma", "TER 12/08"),
    "2026-08-13": (["d3_post.png"], "lote-ago2-transforma", "QUA 13/08"),
    "2026-08-14": (["d4_capa.png", "d4_s2.png", "d4_s3.png", "d4_s4.png"], "lote-ago2-transforma", "QUI 14/08"),
    "2026-08-15": (["d5_post.png"], "lote-ago2-transforma", "SEX 15/08"),
    "2026-08-16": (["d6_post.png"], "lote-ago2-transforma", "SÁB 16/08"),
    "2026-08-17": (["d7_capa.png", "d7_s2.png", "d7_s3.png", "d7_s4.png"], "lote-ago2-transforma", "DOM 17/08"),
    "2026-08-18": (["d1_capa.png", "d1_s2.png", "d1_s3.png", "d1_s4.png"], "lote-ago3-fundo", "SEG 18/08"),
    "2026-08-19": (["d2_post.png"], "lote-ago3-fundo", "TER 19/08"),
    "2026-08-20": (["d3_post.png"], "lote-ago3-fundo", "QUA 20/08"),
    "2026-08-21": (["d4_capa.png", "d4_s2.png", "d4_s3.png", "d4_s4.png"], "lote-ago3-fundo", "QUI 21/08"),
    "2026-08-22": (["d5_post.png"], "lote-ago3-fundo", "SEX 22/08"),
    "2026-08-23": (["d6_post.png"], "lote-ago3-fundo", "SÁB 23/08"),
    "2026-08-24": (["d7_capa.png", "d7_s2.png", "d7_s3.png", "d7_s4.png"], "lote-ago3-fundo", "DOM 24/08"),
    "2026-08-25": (["d1_capa.png", "d1_s2.png", "d1_s3.png", "d1_s4.png"], "lote-ago4-vida", "SEG 25/08"),
    "2026-08-26": (["d2_post.png"], "lote-ago4-vida", "TER 26/08"),
    "2026-08-27": (["d3_post.png"], "lote-ago4-vida", "QUA 27/08"),
    "2026-08-28": (["d4_capa.png", "d4_s2.png", "d4_s3.png", "d4_s4.png"], "lote-ago4-vida", "QUI 28/08"),
    "2026-08-29": (["d5_post.png"], "lote-ago4-vida", "SEX 29/08"),
    "2026-08-30": (["d6_post.png"], "lote-ago4-vida", "SÁB 30/08"),
    "2026-08-31": (["d7_capa.png", "d7_s2.png", "d7_s3.png", "d7_s4.png"], "lote-ago4-vida", "DOM 31/08"),
    "2026-07-02": (["ter07_post_sono.png"], "lote-06-12-jul", "TER 07/07"),
    "2026-07-03": (["qua08_post_voltar.png"], "lote-06-12-jul", "QUA 08/07"),
    "2026-07-04": (["qui09_post1_capa.png", "qui09_post2.png", "qui09_post3.png", "qui09_post4.png"], "lote-06-12-jul", "QUI 09/07"),
    "2026-07-05": (["aprov_teresa_so_deus_basta.png"], "lote-frases-santo", "APROV 18 TERESA SO DEUS BASTA"),
    "2026-07-06": (["sab11_post_sinais.png"], "lote-06-12-jul", "SÁB 11/07"),
    "2026-07-07": (["dom12_post1_capa.png", "dom12_post2.png", "dom12_post3.png", "dom12_post4.png"], "lote-06-12-jul", "DOM 12/07"),
    "2026-07-08": (["seg13_post1_capa.png", "seg13_post2.png", "seg13_post3.png", "seg13_post4.png"], "lote-13-19-jul", "SEG 13/07"),
    "2026-07-09": (["aprov_joao_entardecer.png"], "lote-frases-santo", "APROV 15 JOAO ENTARDECER"),
    "2026-07-10": (["qua15_post1_capa.png", "qua15_post2.png", "qua15_post3.png", "qua15_post4.png"], "lote-13-19-jul", "QUA 15/07"),
    "2026-07-11": (["qui16_post_sede.png"], "lote-13-19-jul", "QUI 16/07"),
    "2026-07-12": (["aprov_teresinha_olhar.png"], "lote-frases-santo", "APROV 16 TERESINHA OLHAR"),
    "2026-07-13": (["sab18_post_refri.png"], "lote-13-19-jul", "SAB 18/07"),
    "2026-07-14": (["dom19_post1_capa.png", "dom19_post2.png", "dom19_post3.png", "dom19_post4.png"], "lote-13-19-jul", "DOM 19/07"),
    # --- Frases dos santos (APROVADAS pelo Felipe: arte final feita no ChatGPT) ---
    "2026-07-15": (["s1_capa.png", "s2.png", "s3.png", "s4.png", "s5.png", "s6.png", "s7.png", "s8.png"], "lote-carrossel-08", "Legenda do post"),  # CARROSSEL #8 distracao (grade 2/sem aprovada 11/07; bumpou APROV 17 JOAO ONDE AMOR)
    "2026-07-16": (["ter14_post_jaculatorias.png"], "lote-13-19-jul", "TER 14/07"),
    "2026-07-17": (["sex17_post_aguas.png"], "lote-13-19-jul", "SEX 17/07"),
    "2026-07-18": (["sex10_post_tristeza.png"], "lote-06-12-jul", "SEX 10/07"),
    "2026-07-19": (["s1_capa.png", "s2.png", "s3.png", "s4.png", "s5.png", "s6.png", "s7.png", "s8.png"], "lote-carrossel-14", "Legenda do post"),  # CARROSSEL #14 filho no colo (bumpou JAC 19 SEDE)
    "2026-07-20": (["jac_tusabes_drama.png"], "lote-frases-santo", "JAC 20 TU SABES"),
    # Slots 19-20/07 em aberto; as demais
    # frases aguardam arte aprovada. Nao agendadas p/ nao publicar versao nao aprovada.
    # "2026-07-19": (["frase05_joao.png"], "lote-frases-santo", "FRASE 05 19/07"),
    # "2026-07-20": (["frase06_teresinha.png"], "lote-frases-santo", "FRASE 06 20/07"),
    # --- Série Santos do Carmelo (arte + mini bio) ---
    "2026-07-21": (["teresa_final.png"], "serie-santos-carmelo", "STA TERESA 21/07"),
    "2026-07-22": (["s1_capa.png", "s2.png", "s3.png", "s4.png", "s5.png", "s6.png", "s7.png", "s8.png"], "lote-carrossel-09", "Legenda do post"),  # CARROSSEL #9 secura (bumpou JAC2 FICA COMIGO)
    "2026-07-23": (["jac2_compaixao.png"], "lote-frases-santo", "JAC2 COMPAIXAO"),
    "2026-07-25": (["jac2_aquem_iremos.png"], "lote-frases-santo", "JAC2 A QUEM IREMOS"),
    "2026-07-26": (["s1_capa.png", "s2.png", "s3.png", "s4.png", "s5.png", "s6.png", "s7.png", "s8.png"], "lote-carrossel-15", "Legenda do post"),  # CARROSSEL #15 microrrezas (bumpou JAC2 CORCA)
    "2026-07-28": (["jac2_arroz.png"], "lote-frases-santo", "JAC2 ARROZ"),
    "2026-07-24": (["joao_final.png"], "serie-santos-carmelo", "SAO JOAO 24/07"),
    "2026-07-27": (["teresinha_final.png"], "serie-santos-carmelo", "STA TERESINHA 27/07"),
    # --- Carrossel "Jaculatorias pra rezar o dia inteiro" (para guardar) ---
    "2026-07-31": (["carrossel/01_capa.png", "carrossel/02_confio.png", "carrossel/03_aumentai_fe.png", "carrossel/04_abba.png", "carrossel/05_espirito.png", "carrossel/06_mae.png", "carrossel/07_sao_jose.png", "carrossel/08_misericordia.png", "carrossel/09_tudo_bem.png", "carrossel/10_fim.png"], "lote-jaculatorias", "CARROSSEL JACULATORIAS"),
}


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
    # anotacoes internas do LEGENDAS.md NUNCA vao pro Instagram:
    # linhas de citacao (>) e linhas de marcacao (**Nota:**, **Obs:**) sao editoriais.
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


def registrar(status):
    log = HERE / "poster_log.txt"
    with open(log, "a", encoding="utf-8") as f:
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


def ja_postado(data):
    return data in _load_state(HERE / "posted.json")


def marcar_postado(data, media_id):
    p = HERE / "posted.json"
    d = _load_state(p)
    d[data] = {"quando": now(), "media_id": media_id}
    _save_state(p, d)


def main():
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    if hoje not in CAL:
        registrar(f"sem conteudo para hoje ({hoje}) — nada postado.")
        return
    if ja_postado(hoje):
        registrar(f"{hoje} ja foi postado antes — pulando (sem republicar).")
        return
    # BACKUP NA NUVEM: se o feed do dia ja esta no ar (o PC do Felipe postou,
    # ou foi manual), registra e sai. Se a checagem falhar, NAO posta (nunca duplicar).
    try:
        secrets = load_secrets()
        if feed_ja_hoje(secrets["IG_USER_ID"], secrets["ACCESS_TOKEN"], hoje):
            marcar_postado(hoje, "ja-no-ar (PC ou manual)")
            registrar(f"{hoje}: feed do dia ja esta no ar backup nao precisou agir.")
            return
    except Exception as e:
        registrar(f"AVISO {hoje}: checagem 'ja no ar' falhou ({repr(e)[:150]}) NAO posto para nao arriscar duplicata.")
        _alerta_falha(f"Feed {hoje} (checagem)", e)
        return
    imgs_rel, lote, secao = CAL[hoje]
    imgs = [str(INSTA / lote / n) for n in imgs_rel]
    faltando = [p for p in imgs if not Path(p).exists()]
    if faltando:
        registrar(f"ERRO {hoje}: imagens faltando: {faltando}")
        return
    try:
        legenda = extrair_legenda(lote, secao)
        media_id = publish(secrets["IG_USER_ID"], imgs, legenda, secrets)
        marcar_postado(hoje, media_id)
        registrar(f"OK {hoje}: publicado ({len(imgs)} img) media_id={media_id}")
        _alerta_ok(f"Feed {hoje} ({secao})", media_id)
    except Exception as e:
        registrar(f"ERRO {hoje}: {repr(e)[:300]}")
        _alerta_falha(f"Feed {hoje}", e)


if __name__ == "__main__":
    main()
