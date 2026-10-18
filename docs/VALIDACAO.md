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

A causa era a tentativa de iniciar uma segunda instância com `omniroute` sem argumentos. O README e os dois prompts de instalação foram corrigidos para verificar a instância existente antes de iniciar e para usar `dashboard` ao abrir o painel. Essa primeira verificação apenas reutilizou a instância existente; ela não devolveu a execução do servidor ao terminal do usuário. Não houve reinstalação, mudança de porta, alteração de credenciais ou modificação do pacote npm.

Essa verificação não enviou requisições de geração aos modelos nem testou a autenticação da conexão OpenRouter. O teste real desse diagnóstico foi feito no Windows; os comandos macOS seguem o mesmo CLI, mas não foram executados em um Mac nessa verificação.

### Restauração da execução no terminal

Após esclarecer que o usuário queria manter o servidor no próprio terminal, a instância em segundo plano foi encerrada com `omniroute stop`. A porta livre foi confirmada antes de executar exatamente `omniroute`, sem argumentos.

O CLI permaneceu em execução, exibiu `OmniRoute is running!` e informou inicialização em 128,2 segundos. Após ficar pronto, `/api/health` retornou `status: "ok"` e `/dashboard/providers/openrouter` respondeu HTTP 200 com o título do OmniRoute. As primeiras sondagens falharam durante a inicialização; o sucesso foi confirmado posteriormente, dentro do prazo configurado de 180 segundos.

A instância de teste foi encerrada pelo comando oficial e a porta 20128 foi novamente conferida livre, permitindo que o usuário inicie o servidor no próprio terminal. Os prompts agora exigem encerrar instâncias temporárias criadas pelos testes. `omniroute dashboard` continua sendo apenas o comando que abre o navegador e retorna ao prompt; ele não transfere uma execução existente para o terminal atual.

## Integração do pool OpenRouter

O perfil router agora encaminha as chamadas pelo filtro local para `/v1/messages` do OmniRoute, qualificando explicitamente os sete IDs com `openrouter/`. O original continua direto na Anthropic. A estratégia `fill-first` é configurada somente no provedor OpenRouter; `main1` tem prioridade 1 e `main2`, quando cadastrada, prioridade 2. O pool usa as conexões do OmniRoute, e não a antiga chave OpenRouter direta do perfil.

A configuração foi aplicada pelo cliente oficial autenticado do OmniRoute e pelos endpoints HTTP de configuração. Foi criada uma chave local restrita aos sete modelos, protegida com DPAPI na instalação Windows. Estratégia/prioridades anteriores e o identificador da chave criada ficaram no backup privado do pool. Nenhum banco foi editado diretamente e nenhum segredo foi incluído no Git.

Foi executada uma chamada real curta, com texto sintético e no máximo oito tokens de saída, para North Mini Code gratuito, pelo caminho filtro → OmniRoute → OpenRouter. Ela retornou HTTP 200 e conteúdo; o cabeçalho de seleção identificou a conexão `main1`. O endpoint `/v1/messages/count_tokens` também retornou HTTP 200 com contagem de entrada. Não foram enviados arquivos nem contexto de projetos.

Os testes do pool usam um servidor OmniRoute simulado para provocar o limite de main1 e verificar main2 antes da reserva de modelo, além de bloquear rotas externas, modelos pagos e repetição por erro de autenticação. Um teste de continuidade usa processos Claude fictícios reais, o hook de limite, a transferência textual e o gateway real do kit para chegar à main2 simulada. Esses testes não substituem testar duas contas reais: a instalação possui somente main1. Main2 não foi criada nem inventada.

As sessões Claude abertas antes da atualização carregam o runtime antigo e precisam ser reabertas. O servidor OmniRoute que já estava ativo foi preservado. O token Claude expirado mostrado no painel é de uma conexão separada e não foi renovado ou usado para contornar o login nativo.

Validação local final: 34 testes do repositório e 21 testes do runtime passaram. O teste de Keychain foi ampliado para a chave local OmniRoute e novamente aprovado em simulação; o acesso interativo real no macOS continua dependente de validação em um Mac.
