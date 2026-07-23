# Santo do dia — São Joaquim e Sant'Ana (26/07)

> PREPARADO e APROVADO pelo Felipe (23/07). Peça EXTRA do dia (não conta como o post nem o story do dia; a fila segue igual). Os dois vão bem cedo (~9h BRT).
> Feed = reel `santa_ana_reel_music.mp4` (com música). Story = `santa_ana_story.png`.
> Ângulo: a fé se aprende por contágio, passada de mão em mão (Ana ensinou Maria). Estilo: sem travessão, sem emoji, sem fórmula-espelho.

## Legenda do post

**Legenda:**
Quase ninguém aprende a rezar num curso. Aprende olhando alguém rezar.

Hoje a Igreja celebra Santa Ana e São Joaquim, os avós de Jesus. Foi na casa deles que Maria cresceu, e foi vendo a mãe rezar que Maria aprendeu a guardar as coisas no coração. A oração que um dia seria a do Magnificat começou pequena, dentro de casa, passada de mão em mão como quem passa um bem de família.

É assim que a fé costuma andar pelo mundo. Não desce pronta do céu para cada um: chega pela avó que rezava o terço na cozinha, pela mãe que fazia o sinal da cruz na sua testa antes de dormir, por alguém comum que rezava perto de você quando você era pequeno. Você talvez reze hoje por causa de gente que nunca vai aparecer em livro nenhum.

E o contrário também é verdade. Alguém está aprendendo a rezar te olhando agora, mesmo sem você perceber. Um filho, um sobrinho, um amigo mais novo na fé. A sua oração escondida está formando alguém.

Experimenta hoje: reza por duas pessoas com nome. Primeiro, agradece por quem te ensinou a rezar, diz o nome dela diante de Deus. Depois, entrega a Deus alguém que está aprendendo a rezar olhando você.

Quem te ensinou a rezar? Deixa o nome aqui embaixo, é uma forma bonita de honrar essa pessoa.

São Joaquim e Santa Ana, avós do Senhor, rogai por nossas famílias.

#vidadeoração #oraçãopessoal #oração #espiritualidade #espiritualidadecatólica #fé #vidaespiritual #santaana #saojoaquim #rezarpelafamília #católico #rezar

## Story (convite)

`santa_ana_story.png` (1080x1920): fundo creme, a imagem devocional (Ana com Maria bebê) no topo, "26 de julho / REZE HOJE COM ELES / São Joaquim e Santa Ana" + frase-âncora (a fé se aprende olhando alguém rezar) + pergunta positiva "Quem te ensinou a rezar? responde aqui" (resposta -> DM).

## Encaixe na automação (santo do dia = EXTRA)

- Regra nova (Felipe 23/07): santo do dia é peça EXTRA. NÃO consome o slot de feed nem o de story do dia; a fila evergreen continua igual. Os dois (reel + story) vão bem cedo (~9h BRT).
- Mecanismo: `poster_santo.py` + `CAL_SANTO` (guard próprio `posted_santo.json`), disparado no início da tarefa da manhã (antes do poster_stories). O feed regular das 12h e o story regular da manhã seguem normais (poster_diario e poster_stories ficam santo-aware e ignoram a peça do santo na checagem "já no ar").
- 26/07 mantém intactos: feed CARROSSEL #15 (12h BRT) + stories s6.png (manhã) e jac2_corca (tarde).
