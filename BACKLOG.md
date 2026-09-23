# GAEA · o que está aberto

Ordem importa: a regra é fechar antes de abrir. Cada item só sai daqui quando estiver
**funcionando e verificado**, não quando estiver codado.

## Para o GAEA contar como terminado

1. **Publicar na VPS** em `GAEA_MODO=producao` — roteiro pronto em [IMPLANTACAO.md](IMPLANTACAO.md).
   Esforço: uma sessão. Depende da VPS.
2. **Fase 2 — o front-end usando a API.** Hoje perfil, pins e avatar vivem no `localStorage`;
   precisam passar pela sessão do servidor, com sincronização e queda para offline.
   É o maior débito técnico atual. Esforço: uma a duas sessões.
3. **Backup restaurado ao menos uma vez** e alertas de 5xx/latência/disco ligados.
   Esforço: meia sessão.

## Na fila, depois disso

### Chat anônimo entre os macacos
*Pedido em 18/09/2026.* Dois macacos conversam sem saber quem é o outro.

Esboço do desenho, para quando chegar a vez:

- **Identidade efêmera**: apelido de sala gerado por sessão (ex.: "macaco-âmbar-7"), sem ligação
  com a conta no que aparece para o outro. O servidor sabe quem é — para moderação e bloqueio —
  mas o par nunca vê. Anonimato entre usuários, não anonimato perante o serviço; a diferença
  precisa estar escrita na tela.
- **Escopo da conversa**: sala por lugar (o parque, a praça) ou par a par por proximidade.
  Sala pública é mais fácil de moderar que DM.
- **Retenção curta**: mensagem some em horas, como a presença some em 5 minutos.
- **Moderação desde o primeiro commit**, não depois: limite de taxa por conta, botão de denunciar
  e bloquear, palavra-chave para autolesão com encaminhamento ao CVV (188), e corte de menor de
  idade no cadastro. Anonimato somado a localização e a estranhos é exatamente a combinação que
  dá errado quando a moderação vem depois — se não der para fazer direito, é melhor não ter.
- **Sem localização na conversa**: a sala já implica a região; a mensagem não carrega coordenada.
- **Registro**: quem denuncia e quem é denunciado entram na auditoria encadeada que já existe.

Esforço estimado: duas sessões para o mecanismo, mais uma para moderação e testes.

### Cache próprio da Overpass
A API pública limita por IP e devolve 429/504 com poucos usuários simultâneos. Um container
`overpass-api/db` regional ou cache em disco com TTL de horas resolve. Vira obrigatório no dia
em que houver mais de um punhado de pessoas usando ao mesmo tempo.
