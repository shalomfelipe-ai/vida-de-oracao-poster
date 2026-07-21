#!/usr/bin/env python3
"""
Transforma um card Carmelo (1080x1350 ou 1080x1920) num REEL 9:16 (1080x1920)
com movimento sutil (zoom lento estilo Ken Burns) e, opcionalmente, musica.

- Fundo = a propria arte, ampliada pra preencher 9:16, desfocada e levemente
  escurecida (fica no clima da paleta sem barra preta feia).
- Frente = o card inteiro, centralizado.
- Movimento = zoom lento (1.00 -> ~1.06) ao longo do video.
- Audio = --musica arquivo.mp3 (corta/estica pra duracao, com fade out).
  Sem musica, gera trilha silenciosa (o mp4 sai com stream de audio valido).

Uso:
  python3 produzir_reel.py --card capa.png --saida reel.mp4 --dur 12
  python3 produzir_reel.py --card capa.png --musica trilha.mp3 --dur 15 --saida reel.mp4

Specs de Reels (Meta): mp4 H.264 + AAC, 1080x1920 (9:16), 3s a 15min, 30fps.
Docs: https://developers.facebook.com/docs/instagram-platform/content-publishing/
"""
import argparse, subprocess, sys, tempfile, os
from pathlib import Path
from PIL import Image, ImageFilter

W, H = 1080, 1920          # canvas final do reel
SS = 2                     # supersampling p/ o zoom nao borrar (render 2x)


def montar_base(card_path: Path, saida_png: Path):
    """Compoe o quadro-base 9:16 (fundo desfocado + card centralizado) em alta res."""
    bw, bh = W * SS, H * SS
    card = Image.open(card_path).convert("RGB")

    # --- fundo: cobre 9:16 e desfoca ---
    cw, ch = card.size
    escala = max(bw / cw, bh / ch)
    fundo = card.resize((int(cw * escala), int(ch * escala)), Image.LANCZOS)
    # corta centralizado pra exatamente bw x bh
    x = (fundo.width - bw) // 2
    y = (fundo.height - bh) // 2
    fundo = fundo.crop((x, y, x + bw, y + bh))
    fundo = fundo.filter(ImageFilter.GaussianBlur(radius=42 * SS))
    # escurece um tico pra arte da frente destacar
    escuro = Image.new("RGB", fundo.size, (0, 0, 0))
    fundo = Image.blend(fundo, escuro, 0.28)

    # --- frente: card inteiro, ~90% da largura ---
    alvo_w = int(bw * 0.90)
    escala_f = alvo_w / cw
    frente = card.resize((alvo_w, int(ch * escala_f)), Image.LANCZOS)
    fx = (bw - frente.width) // 2
    fy = (bh - frente.height) // 2
    fundo.paste(frente, (fx, fy))

    fundo.save(saida_png, quality=95)
    return saida_png


def render(base_png: Path, saida_mp4: Path, dur: float, musica: Path | None, fps: int = 30):
    frames = int(dur * fps)
    zoom = ("zoompan=z='min(1.00+on/{n}*0.06,1.06)'"
            ":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            ":d={n}:s={w}x{h}:fps={fps}").format(n=frames, w=W, h=H, fps=fps)

    # TODOS os inputs primeiro; depois o filtro; depois os -map (regra do ffmpeg)
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(base_png)]
    if musica:
        cmd += ["-i", str(musica)]
        af = f"[1:a]afade=t=out:st={max(dur-1.2,0):.2f}:d=1.2,atrim=0:{dur:.2f}[a]"
        fc = f"[0:v]{zoom},format=yuv420p[v];{af}"
        amap = "[a]"
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        fc = f"[0:v]{zoom},format=yuv420p[v]"
        amap = "1:a"

    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", amap, "-shortest",
            "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-r", str(fps), "-t", f"{dur:.2f}",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-movflags", "+faststart", str(saida_mp4)]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, help="PNG do card aprovado")
    ap.add_argument("--saida", required=True, help="mp4 de saida")
    ap.add_argument("--dur", type=float, default=12.0, help="duracao em segundos")
    ap.add_argument("--musica", default=None, help="mp3/m4a opcional")
    a = ap.parse_args()

    card = Path(a.card)
    if not card.exists():
        sys.exit(f"ERRO: card nao encontrado: {card}")
    musica = Path(a.musica) if a.musica else None
    if musica and not musica.exists():
        sys.exit(f"ERRO: musica nao encontrada: {musica}")

    with tempfile.TemporaryDirectory() as td:
        base = montar_base(card, Path(td) / "base.png")
        render(base, Path(a.saida), a.dur, musica)
    print(f"OK: {a.saida}")


if __name__ == "__main__":
    main()
