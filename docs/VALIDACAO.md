# Validação da versão inicial — 18/10/2026

- Windows: 20 testes do repositório passaram, incluindo instalação em usuário temporário, reinstalação, reversão, preservação de arquivos não relacionados, proteção contra destinos externos, configuração persistente do OmniRoute e roteamento pelos IDs originais.
- Windows: 21 testes do runtime passaram, incluindo troca de sessão por limite com processo fictício real, filtro gratuito, reservas, isolamento de variáveis, DPAPI e bloqueio de encerramento quando há trabalho em andamento.
- Instalação Windows existente: 16 verificações passaram depois do ajuste de nomes e arquivamento da cópia de referência. O diagnóstico nativo do perfil router terminou com código zero, sem aviso de settings; sete opções e seus IDs foram conferidos.
- Auditoria de arquivos públicos passou. Settings privados, MCP autenticado, logs, histórico, bancos e segredos não foram incluídos no bundle. Referências pessoais e de clientes identificadas foram removidas ou generalizadas.
- A sintaxe do instalador PowerShell foi validada. Não houve geração real de modelos nem publicação no GitHub nesta preparação.
- macOS: implementado Keychain por entrada padrão e supervisão por ps; testes simulados desses caminhos passaram no Windows. O fluxo completo depende de execução no runner macOS e teste real de Keychain/Claude. A CI incluída executa as suites nas duas plataformas, mas não foi executada remotamente porque o repositório ainda é local.

Os testes locais não comprovam a disponibilidade atual de todos os provedores. O runtime revalida o catálogo ao abrir e durante o uso; consulte as restrições e datas em README.md. Nenhuma restrição externa foi contornada.
