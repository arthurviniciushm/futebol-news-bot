# Futebol News Bot

Automação para monitorar uma lista do X, transformar notícias em posts em português e enviar o resultado para o Telegram.

## Fluxo

X List → GitHub Actions → IA → Telegram

O computador do usuário não precisa ficar ligado. O workflow roda na infraestrutura do GitHub.

## Configuração necessária

Crie estes GitHub Actions Secrets em **Settings → Secrets and variables → Actions → New repository secret**:

- `X_AUTH_TOKEN` — cookie `auth_token` de uma conta do X usada para acessar a lista.
- `X_CT0` — cookie `ct0` da mesma conta.
- `TELEGRAM_BOT_TOKEN` — token do bot criado no BotFather.
- `TELEGRAM_CHAT_ID` — ID numérico do chat que receberá as notícias.
- `GEMINI_API_KEY` — chave da API do Google Gemini.

### Importante sobre os cookies do X

Use, de preferência, uma conta secundária. Os cookies `auth_token` e `ct0` são credenciais de sessão e devem ser tratados como senhas. Nunca coloque esses valores em arquivos do repositório.

## Lista monitorada

A configuração atual usa:

`https://x.com/i/lists/1305205166652694534`

## Funcionamento

O workflow executa a cada 10 minutos. Ele abre a lista com Playwright, coleta os posts visíveis, compara com `state.json`, manda somente posts novos para o Gemini e envia os textos gerados ao Telegram.

No primeiro uso, o bot pode processar os posts atualmente visíveis da lista. Depois disso, apenas novos IDs são processados.

## Telegram

Crie um bot pelo `@BotFather`, envie uma mensagem para ele e descubra seu `chat_id`. O `@arthurviniciushm` é seu usuário do Telegram, mas não substitui o token do bot nem necessariamente o chat ID numérico.

## IA

O projeto usa Gemini via API. A disponibilidade e os limites gratuitos da API podem mudar; nenhuma chave é armazenada no código.

## Execução manual

Depois de configurar os secrets, vá em **Actions → Monitorar lista do X → Run workflow**.
