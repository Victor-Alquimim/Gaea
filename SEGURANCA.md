# GAEA · segurança da informação

Plano e estado real dos controles para o app sair do `localhost` e ir para a internet.
Escrito no vocabulário do **CID** (confidencialidade, integridade, disponibilidade) e mapeado
para **ISO/IEC 27001:2022** (o sistema de gestão) e **ISO/IEC 27002:2022** (os controles).

> Uma honestidade necessária: código não certifica ninguém. A 27001 certifica uma
> **organização** que roda um SGSI — política aprovada, escopo, análise de risco, Declaração
> de Aplicabilidade, auditoria interna, análise crítica pela direção. O que dá para fazer em
> software é implementar os controles da 27002 e deixar evidência auditável de cada um. É
> isso que está feito aqui; a parte organizacional está listada como pendente, com dono e
> ordem.

---

## 1. Arquitetura alvo

```
            navegador
                │  HTTPS (TLS 1.3, HSTS)
                ▼
      proxy reverso / WAF            ← termina TLS, limita taxa, bloqueia padrões conhecidos
                │  HTTP local
                ▼
        gaea_api.py (app)            ← sessão, autorização, validação, auditoria, retenção
          │            │
          ▼            ▼
      SQLite/WAL    backup cifrado   ← Postgres quando passar de ~50 req/s ou exigir réplica
      (volume)      (fora do host)
                │
                ▼
         fontes externas             ← Overpass, Nominatim, GIBS, Commons: só leitura, sem credencial
```

O app é servido pelo mesmo processo que a API — origem única, o que elimina CORS e
simplifica cookie e CSP. As chaves de API de terceiros continuam **no navegador do usuário**:
o servidor nunca as vê, então não há segredo de cliente para vazar aqui.

---

## 2. O CID aplicado a este app

| | O que significa no GAEA | Como está garantido |
|---|---|---|
| **Confidencialidade** | Posição de pessoa é o dado mais sensível que tratamos. Ninguém além do dono vê pin, nota ou e-mail; no mapa social sai só o que a pessoa autorizou, na precisão que ela escolheu. | Sessão obrigatória, `conta_id` no `WHERE` de toda consulta, precisão arredondada no cliente **antes** do envio, IP e user-agent só como HMAC, senha só como PBKDF2 |
| **Integridade** | O que está gravado é o que aconteceu: ninguém altera pin alheio, ninguém falsifica identidade no mapa, e o log não pode ser reescrito sem deixar rastro. | Identidade da presença vem da sessão (o corpo do pedido é ignorado), CSRF de dupla submissão, verificação de origem, validação estrita de entrada, auditoria encadeada por SHA-256 |
| **Disponibilidade** | O mapa continua no ar sob abuso, e um desastre não leva os dados junto. | Balde de fichas por IP e rota, bloqueio progressivo de login, tetos de corpo e de presenças, SQLite em WAL, backup consistente por API + `integrity_check` |

---

## 3. Classificação da informação

| Dado | Classificação | Onde vive | Retenção |
|---|---|---|---|
| E-mail, nome | Pessoal | `contas` | Enquanto a conta existir |
| Senha | Credencial | `contas` (PBKDF2, 260k iterações, sal por conta) | Idem — nunca em texto |
| Token de sessão | Credencial | Só o **hash** em `sessoes`; o valor vive no cookie | 7 dias, revogável |
| Posição no mapa social | **Pessoal sensível** (localização) | `presenca` | **5 minutos** sem atualização |
| Pins e notas | Pessoal | `pins` | Enquanto a conta existir |
| IP, user-agent | Pessoal | `sessoes`, `auditoria` — só HMAC truncado | 1 ano (auditoria) |
| Chaves de API de terceiros | Segredo do usuário | `localStorage` do navegador | Até ele apagar |
| Dados de fluxo (OSM, CSV) | Público / agregado | `data/` | Sem prazo |

---

## 4. Controles implementados (27002:2022)

Cada linha tem um teste em `servidor/testes.py` — `python servidor/testes.py` imprime o
controle ao lado do resultado. Hoje: **36 verificações, 0 falhas**.

| Controle | O que foi feito | Onde |
|---|---|---|
| 5.15 / 8.3 Controle de acesso | Toda leitura e escrita filtra por `conta_id`; pin de outro devolve 404, não 403 (não confirma existência) | `armazenamento.py`, `gaea_api.py` |
| 5.16 Gestão de identidade | Registro com e-mail único, id opaco, sessão emitida na criação | `r_registrar` |
| 5.17 Informação de autenticação | PBKDF2-HMAC-SHA256 260k + sal por conta; mínimo de 10 caracteres; erro neutro no login | `seguranca.py` |
| 8.2 Direitos privilegiados | `/api/admin/integridade` exige token próprio (`GAEA_ADMIN_TOKEN`) | `r_integridade` |
| 8.5 Autenticação segura | Token de 256 bits, guardado só como HMAC; cookie `HttpOnly`; bloqueio após N tentativas; troca de senha revoga todas as sessões | `gaea_api.py` |
| 8.6 Gestão de capacidade | Balde de fichas por IP e rota; tetos de corpo (16 KB) e de presenças simultâneas | `seguranca.Limitador` |
| 8.9 Gestão de configuração | Toda configuração por variável de ambiente; produção falha ao subir sem segredo, HTTPS e TLS na borda | `config.py` |
| 8.10 Exclusão de informação | Zelador roda a cada minuto e apaga presença vencida, sessão expirada e auditoria além do prazo | `Banco.purgar` |
| 8.11 Mascaramento | IP e user-agent viram HMAC truncado; log de acesso é escrito sem query string | `seguranca.pseudonimiza` |
| 8.12 Prevenção de vazamento | Resposta de erro nunca traz stack; mensagem de registro duplicado é neutra | `_rota` |
| 8.13 Cópias de segurança | Backup pela API do SQLite (consistente com o banco em uso) + `PRAGMA integrity_check` | `Banco.backup` |
| 8.15 Registro de eventos | Auditoria append-only encadeada por hash; adulterar uma linha quebra a cadeia e a verificação acusa o `seq` | `Banco.audita`, `verifica_auditoria` |
| 8.16 Monitoramento | `/api/saude` público e `/api/admin/integridade` com métricas e estado da cadeia | `gaea_api.py` |
| 8.23 Filtragem web | CSP com `frame-ancestors 'none'`, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` (geolocalização só para a própria origem), HSTS quando há TLS | `seguranca.cabecalhos` |
| 8.24 Criptografia | `hmac.compare_digest` em toda comparação sensível; segredo fora do código | `seguranca.py` |
| 8.26 Requisitos de aplicação | CSRF de dupla submissão + verificação de `Origin`; cookies `SameSite=Strict` | `_protege_escrita` |
| 8.28 Codificação segura | Validação estrita de tipo e faixa; SQL sempre parametrizado; roteamento por lista fechada | todo o servidor |
| LGPD art. 18 V e VI | `GET /api/conta/exportar` e `DELETE /api/conta` (apaga pins, sessões e presença por cascata) | `r_exportar`, `r_apagar_conta` |

---

## 5. Riscos principais e tratamento

| Risco | Impacto | Prob. | Tratamento | Estado |
|---|---|---|---|---|
| Vazamento de localização de um usuário | Alto | Média | Consentimento explícito, precisão padrão de ~500 m, TTL de 5 min, sem histórico de trajeto | **Mitigado** |
| Roubo de sessão por XSS | Alto | Baixa | CSP restritiva, cookie `HttpOnly`, sem `innerHTML` de dado remoto sem escape | **Mitigado** — falta auditoria de XSS no front (F2) |
| Força bruta de senha | Médio | Alta | Bloqueio por conta + limite por IP + PBKDF2 caro | **Mitigado** |
| Perda do banco | Alto | Baixa | Backup por API + verificação de integridade | **Parcial** — falta backup fora do host e teste de restauração |
| Abuso das APIs de terceiros com a chave do usuário | Médio | Média | Chave só no navegador dele, restrição por referenciador orientada na UI | **Aceito com orientação** |
| Indisponibilidade por enxurrada | Médio | Média | Limitador no app | **Parcial** — falta WAF/CDN na borda |
| Senha reaproveitada de outro vazamento | Médio | Alta | Mínimo de 10 caracteres, lista curta de senhas óbvias | **Parcial** — falta checagem contra k-anonymity do HIBP |

---

## 6. Plano por fases

**Fase 1 — fundação (feita nesta sessão)**
Configuração por ambiente, SQLite com esquema e retenção, sessão e senha, autorização por
dono, CSRF e origem, limitação de taxa, cabeçalhos, auditoria encadeada, backup, exportação
e eliminação de conta, 36 testes de controle.

**Fase 2 — o app usando a API** (próximo passo natural)
`js/nuvem.js` como adaptador: perfil passa a autenticar no servidor, pins e avatar sincronizam,
presença usa a sessão. O modo local-first continua como *fallback* offline. Inclui varredura de
XSS no front (todo dado vindo do servidor já passa por `esc()`, falta revisar caso a caso).

**Fase 3 — infraestrutura de produção**
Domínio, TLS 1.3 com renovação automática, proxy reverso (nginx/Caddy) com WAF e limite de
taxa na borda, Postgres quando a carga pedir, backup cifrado fora do host com **teste de
restauração mensal**, monitoramento com alerta (saúde, latência, 5xx, taxa de 401/429),
CI rodando `servidor/testes.py` a cada commit, varredura de dependências.

**Fase 4 — SGSI (organizacional, ISO 27001 cláusulas 4 a 10)**
Escopo e contexto, política aprovada pela direção, inventário de ativos, análise e plano de
tratamento de risco, Declaração de Aplicabilidade, gestão de acessos com revisão trimestral,
plano de resposta a incidente com prazo de notificação à ANPD (LGPD art. 48), treinamento,
auditoria interna e análise crítica. Sem isso não há certificação — só um app bem feito.

---

## 7. Checklist de subida

```bash
export GAEA_MODO=producao
export GAEA_SEGREDO="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export GAEA_ORIGEM="https://gaea.seudominio.com.br"
export GAEA_TLS_BORDA=1
export GAEA_ADMIN_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
export GAEA_BANCO=/var/lib/gaea/gaea.db
python servidor/gaea_api.py
```

Antes de apontar o DNS:

- [ ] `python servidor/testes.py` verde no ambiente de destino
- [ ] TLS com nota A no SSL Labs, HSTS ligado, redirecionamento 80 → 443
- [ ] Proxy repassa `X-Forwarded-For` (o limitador depende disso para não punir todo mundo pelo IP do proxy)
- [ ] Backup agendado **fora** do host e restauração testada uma vez
- [ ] Alertas de 5xx, latência e disco
- [ ] Política de privacidade publicada, com a base legal do consentimento para geolocalização
- [ ] Encarregado (DPO) nomeado e canal de contato publicado
- [ ] `GAEA_SEGREDO` e `GAEA_ADMIN_TOKEN` em cofre, nunca em arquivo versionado

---

## 8. Como verificar

```bash
python servidor/testes.py                              # 36 controles, com o número ISO ao lado
curl -H "X-GAEA-ADMIN: $GAEA_ADMIN_TOKEN" .../api/admin/integridade
```

A resposta de integridade traz `integrity_check` do SQLite, o estado da cadeia de auditoria e
as métricas do serviço. Se `auditoria_ok` vier `false`, alguém mexeu no log: o campo
`auditoria_quebrada_em` diz em qual evento a cadeia parou de fechar.
