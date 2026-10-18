# Validação — 18/10/2026

## Preparação local inicial

- Windows: 20 testes do repositório passaram, incluindo instalação em usuário temporário, reinstalação, reversão, preservação de arquivos não relacionados, proteção contra destinos externos, configuração persistente do OmniRoute e roteamento pelos IDs originais.
- Windows: 21 testes do runtime passaram, incluindo troca de sessão por limite com processo fictício real, filtro gratuito, reservas, isolamento de variáveis, DPAPI e bloqueio de encerramento quando há trabalho em andamento.
- Instalação Windows existente: 16 verificações passaram depois do ajuste de nomes e arquivamento da cópia de referência. O diagnóstico nativo do perfil router terminou com código zero, sem aviso de settings; sete opções e seus IDs foram conferidos.
- Auditoria de arquivos públicos passou. Settings privados, MCP autenticado, logs, histórico, bancos e segredos não foram incluídos no bundle. Referências pessoais e de clientes identificadas foram removidas ou generalizadas.
- A sintaxe do instalador PowerShell foi validada. Não houve geração real de modelos nem publicação no GitHub nesta preparação.
- macOS: implementado Keychain por entrada padrão e supervisão por ps; testes simulados desses caminhos passaram no Windows na preparação inicial. Esses testes isolados não validam o login interativo nem o armazenamento/acesso real no Keychain.

Os testes locais não comprovam a disponibilidade atual de todos os provedores. O runtime revalida o catálogo ao abrir e durante o uso; consulte as restrições e datas em README.md. Nenhuma restrição externa foi contornada.

## Publicação e CI

O repositório foi publicado no GitHub. A [primeira execução da CI](https://github.com/matheusdavipc-ai/Claude-Antigravity-Kit/actions/runs/39157803472), correspondente ao commit `4a9528c`, terminou com sucesso nos jobs Windows e macOS. O runner executou a auditoria e as suites automatizadas; os provedores são simulados e não houve geração real de modelos.

A aprovação da CI no macOS não comprova o fluxo completo com uma conta Anthropic, as autorizações interativas do Keychain ou uma sessão nativa de Claude em um Mac real. Essas verificações continuam pendentes. A inspeção visual interativa do perfil instalado também depende de autorização legítima de confiança na pasta; essa autorização não foi contornada.

A documentação de instalação e o catálogo descrevem os recursos distribuídos. Exemplos de uso não representam execuções reais nem comprovação de disponibilidade atual dos modelos.

## Diagnóstico de porta ocupada do OmniRoute

Na instalação Windows, o aviso de porta 20128 ocupada foi investigado. O processo que escutava em `127.0.0.1:20128` era o servidor Node do pacote OmniRoute, iniciado por `omniroute serve --no-open`.

- `/api/health` respondeu HTTP 200 com `status: "ok"`.
- A página inicial e `/dashboard/providers/openrouter` responderam HTTP 200 com o título do OmniRoute.
- `omniroute dashboard` terminou com código zero e acionou a abertura do painel no navegador.
- Depois do comando, havia um único processo escutando nessa porta, com o mesmo PID e endereço local de antes; a saúde continuou positiva.

A causa era a tentativa de iniciar uma segunda instância com `omniroute` sem argumentos. O README e os dois prompts de instalação foram corrigidos para verificar a instância existente antes de iniciar e para usar `dashboard` ao abrir o painel. Não foi necessário reinstalar, mudar a porta, encerrar o servidor, alterar credenciais ou modificar o pacote npm.

Essa verificação não enviou requisições de geração aos modelos nem testou a autenticação da conexão OpenRouter. O teste real desse diagnóstico foi feito no Windows; os comandos macOS seguem o mesmo CLI, mas não foram executados em um Mac nessa verificação.
