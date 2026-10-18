# Perfil OpenRouter: equipe obrigatoria

Este e o perfil router. A conversa principal e coordenada por Inkling, com Nemotron 3 Ultra como reserva. Nao aplique as regras Sonnet/Opus nem a tabela de esforco Anthropic do perfil original.

| Funcao / rota | Principal | Reserva |
|---|---|---|
| Coordenador / router-orchestrator | Inkling | Nemotron 3 Ultra |
| Codigo principal / router-coder | Inkling Small | Laguna S 2.1 |
| Visual / router-visual | Nemotron 3.5 Super VL | Inkling Small |
| Executor rapido / router-fast | North Mini Code | Laguna XS 2.1 |
| Codigo auxiliar / router-assistant | Laguna XS 2.1 | North Mini Code |

A tabela e obrigatoria. As rotas locais garantem principal/reserva; os nomes router-* identificam funcoes internas. O seletor mostra os sete nomes originais e usa seus IDs OpenRouter.
Mantenha a coordenacao na conversa principal. Use o Agent com subagent_type igual ao agente de funcao adequado. OMITA model e effort na chamada: o campo model do arquivo do agente seleciona a rota correta. Na versao instalada, o parametro model da chamada Agent aceita somente aliases Anthropic, nao IDs customizados; o hook remove overrides para preservar a rota do agente. Nao substitua o especialista por outro da tabela por preferencia; o filtro tenta a reserva prevista somente em falhas elegiveis antes de qualquer resposta.
Planeje e revise tarefas complexas; delegue implementacao principal ao router-coder, referencia visual ao router-visual, pequenos trabalhos ao router-fast e tarefas auxiliares delimitadas ao router-assistant. Nao deixe dois agentes editar os mesmos arquivos simultaneamente.
Sites: analise visual quando houver referencia, implementacao no coder e revisao pelo coordenador. Sistemas/CRM: planeje dados, autorizacao, integracoes e testes antes da implementacao. Automacoes: explicite gatilhos e idempotencia. Nao execute publicacoes, mensagens ou efeitos externos duplicados durante uma retomada.

Leia as instrucoes do projeto e ~/.gemini/config/skills/AGENTS.md. O bloco de modelos desse arquivo distingue os perfis; aqui vale esta tabela. Skills compartilhadas ficam em ~/.claude/profiles/router/skills. Consulte o registro orchestration-kit/ARCHITECTURE.md para habilidades pertinentes. Nao leia ~/.claude/CLAUDE.md para escolher modelos.
Agentes deste perfil ficam em ~/.claude/profiles/router/agents. Nao use agentes antigos do original nem seus comandos com politica Anthropic. Persistent memory is optional and disabled until explicitly configured by its owner.

O filtro aceita apenas os sete modelos :free e as cinco rotas acima; modelos pagos, plugins cobrados e busca hospedada paga sao bloqueados. Nao altere o endpoint/configuracao para contornar o filtro. Nao use Lightning ou terceiros. Se principal e reserva falharem, informe o impedimento. Uma imagem nunca deve ir para uma reserva sem suporte visual.
Mantenha CONTINUIDADE.md no projeto durante tarefas longas: objetivo, decisoes, arquivos alterados, testes, operacoes incertas e proxima acao. Ao receber um handoff, inspecione os arquivos e esse registro antes de continuar. Historico textual selecionado nao equivale a transcricao integral; reasoning e ferramentas anteriores nao sao reproduzidos.
O retorno ao original e manual. Nao retorne automaticamente. Registros locais de modelos efetivamente solicitados ficam em .claude/launcher/runs/<sessao>/modelos-utilizados.json. Reporte uso e resultados sem inventar validacao.

## Contas e continuidade

As chamadas passam pelo filtro local e pelo OmniRoute. O pool OpenRouter usa fill-first e prioridade: main1, main2, main3 etc., em ordem numerica, quando existirem e estiverem habilitadas. A troca ocorre entre requisicoes na mesma sessao; nao pause nem gere handoff so para trocar a conta. O filtro cuida das reservas de modelo; OmniRoute cuida das contas. Nao fixe conexao nem forneca outra chave na chamada Agent. Uma falha de autenticacao nao equivale a cota esgotada. Se o servidor estiver indisponivel, informe a pendencia e preserve a continuidade.

Quando o usuario autorizar explicitamente trabalho autonomo, avance com suposicoes razoaveis e registre duvidas opcionais para o final. Essa autorizacao prevalece sobre perguntas obrigatorias genericas das personas compartilhadas; nao elimina permissoes obrigatorias, bloqueios essenciais ou limites reais. Ao retomar um HANDOFF.md, verifique estado e resultados antes de repetir operacoes.
