# Poster backup na nuvem (GitHub Actions) do @felipebzr_

O PC do Felipe continua sendo o TITULAR (tarefas do Windows 9h/12h/17h BRT).
Este repositorio e o RESERVA: roda 45 min depois de cada slot e, antes de
postar, pergunta a propria API do Instagram se o conteudo do dia ja esta no
ar. Se estiver (PC funcionou ou post manual), ele NAO faz nada. Se nao
estiver (PC desligado/travado), ele publica. Nunca duplica.

## Setup (uma vez, ~15 min)

1. Crie um repositorio PRIVADO no github.com (ex.: `vida-de-oracao-poster`).
2. Suba TODO o conteudo desta pasta para o repositorio, com a estrutura
   intacta (o `.github/workflows/poster.yml` precisa estar nesse caminho).
   O jeito mais facil no Windows e o GitHub Desktop:
   File > New repository (aponte para uma copia desta pasta) > Publish
   repository (marque "Keep this code private").
3. No site do GitHub: Settings > Secrets and variables > Actions >
   New repository secret. Crie DOIS segredos, copiando os valores do
   arquivo `secrets.json` do PC (pasta instagram/api-setup — NAO suba
   esse arquivo pro GitHub):
   - `IG_USER_ID`
   - `ACCESS_TOKEN`
4. Aba Actions > habilite os workflows se o GitHub pedir.

## Testar sem risco

Aba Actions > poster-backup > Run workflow > modo `manha` (rode DEPOIS que o
story da manha ja estiver no ar). Resultado esperado no log:
"story do slot ja esta no ar backup nao precisou agir". Isso prova o circuito
inteiro (token, API, checagem) sem postar nada.

## Avisos

- O agendador do GitHub pode atrasar alguns minutos (normal, ate ~30 min).
- O TOKEN expira ~60 dias depois de gerado (o atual e de 01/07/2026, vale ate
  ~30/08/2026). Se a viagem passar disso, rode `renovar_token.py` no PC antes
  e atualize o segredo `ACCESS_TOKEN` no GitHub.
- Conteudo novo (proximos lotes aprovados): copiar a pasta do lote para o
  repositorio, atualizar os calendarios CAL/CAL_S nos scripts em `api-setup/`
  e dar commit/push ANTES da data.
- O estado (posted.json, stories_posted.json, logs) fica commitado no proprio
  repositorio pelo workflow; para conferir o que o backup fez, veja esses
  arquivos ou a aba Actions.
