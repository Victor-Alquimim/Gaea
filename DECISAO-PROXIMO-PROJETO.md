# Terminar o GAEA vs. começar o LKF + Diário

Avaliação de esforço e custo pedida em 18/09/2026. Unidade de esforço: **sessão** — um bloco
nosso de trabalho como os desta semana, que costuma render um módulo inteiro funcionando e
testado.

---

## A — Terminar o GAEA

| Item | Esforço | Custo em dinheiro | Risco |
|---|---|---|---|
| Publicar na VPS em produção | 1 sessão | R$ 30–60/mês + domínio ~R$ 40/ano | baixo — roteiro pronto e testado |
| Fase 2: front-end usando a API | 1–2 sessões | zero | médio — mexe em código que já funciona |
| Backup restaurado + alertas | ½ sessão | zero | baixo |
| **Total** | **2,5–3,5 sessões** | **~R$ 60/mês** | **baixo** |

Depois disso, opcional: chat anônimo (3 sessões, sendo 1 só de moderação) e cache próprio da
Overpass (1 sessão) — ambos em [BACKLOG.md](BACKLOG.md).

O risco real aqui não é técnico, é de dependência externa: a Overpass pública limita por IP.
Enquanto for você e mais alguns, tudo bem.

---

## B — LKF + Diário storage no HDD de 1 TB

Quebrando em quatro partes, porque elas têm dificuldades muito diferentes:

### B1 · Artefato portátil (o HDD que roda sozinho)
Executável único no disco, dados ao lado dele, sem instalar nada na máquina anfitriã.
**Já sabemos fazer:** é exatamente o padrão do `GAEA.exe` que ficou pronto hoje.
→ **0,5 a 1 sessão.** Custo zero.

### B2 · Diário storage (o "SharePoint no HDD")
Ingestão de arquivos, hash e dedupe, metadados e tags, versões por conteúdo, busca full-text
(SQLite FTS5, que já vem no Python), extração de texto de PDF/DOCX, interface web local, cifra
do volume (BitLocker To Go ou VeraCrypt).
→ **3 a 4 sessões.** Custo zero em software.

### B3 · O SLM que "nasce e se molda no dispositivo"
Aqui mora a diferença de ordem de grandeza, e vale separar quatro coisas que costumam ser
confundidas:

| Caminho | O que é | Viável no seu HDD? | Esforço |
|---|---|---|---|
| **Rodar modelo pequeno aberto** | Qwen2.5 1.5B, Llama 3.2 1B/3B, Gemma 2 2B em GGUF Q4 (0,7–2,5 GB) via llama.cpp — binário único, cabe no disco | **Sim.** 15–30 tok/s num 1B em CPU decente; 5–15 num 3B | 1 sessão |
| **Moldar com o seu diário (RAG)** | Índice de embeddings + FTS5 sobre os seus arquivos; o modelo responde citando o que é seu | **Sim, e é o caminho certo.** Modelo de embedding ~100 MB | 1,5–2 sessões |
| **Fine-tune LoRA** | Ajustar de fato os pesos com os seus textos | **Só com GPU** de 8–12 GB VRAM (ou Mac com memória unificada). 1–3 h por rodada num 1B. Em CPU pura, 10–50× mais lento: inviável como rotina | 1–2 sessões + hardware |
| **Treinar do zero** | Um modelo nascido ali dentro | **Não.** Um 1B minimamente útil custa dezenas de milhares de dólares em GPU-hora e trilhões de tokens | — |

Ou seja: "nascer dentro do dispositivo" no sentido literal está fora; "se moldar ao que é seu"
está ao alcance hoje, por RAG, e opcionalmente por LoRA se houver GPU.

Um detalhe físico que muda a experiência: HDD externo USB lê a ~100–150 MB/s, então carregar um
modelo de 2 GB leva uns 15–25 s no primeiro uso (depois o sistema mantém em RAM). Um **SSD
externo** (R$ 300–500 por 1 TB) corta isso para 2–3 s e muda a sensação do artefato inteiro.
→ **B3 total: 2 a 3 sessões.** Custo: zero em software; R$ 300–500 se quiser o SSD.

### B4 · Governança LKF — agora com o material na mão

Li `Documents\Projetos\LKF`. LKF é o **Learning & Knowledge Framework**, uma camada do
**LyraOS**, que é um *Knowledge Operating System* — especificação, não software. Três gerações:
v1.0 fragmentado em seis documentos, v2.0 consolidado em arquivo único, v3.0 "epistemic
hardened". A v3.0 nasceu de um incidente concreto: a v2.0 deixou um Architect de IA fabricar um
estudo de caso, e a correção foi inserir um portão obrigatório no pipeline.

O que a especificação define, e o que dela **vira código determinístico**:

| Elemento da spec | Como se implementa | Esforço |
|---|---|---|
| Gate **JUSTIFY** (Provenance, Confidence 1–5, Method) | `CHECK` no banco + máquina de estados: artefato não chega a `Active` sem os três campos | baixo |
| **Knowledge Graph** (nós, arestas tipadas: Prerequisite, Continuation, Reference, Dependency) | duas tabelas + metadados de proveniência e confiança na aresta | baixo |
| **Validation** (DuplicateContent/MissingContext/BrokenNavigation: Reject) | validadores executáveis, no mesmo formato dos 36 testes do GAEA | médio |
| **Axioma XVI — Mortality** (componente sem teste por 2 ciclos → `Deprecated`) | o mesmo zelador de retenção que já roda no GAEA | baixo |
| **Category 1 — Fabricação** → auditoria recursiva dos dependentes | caminhada no grafo + a trilha encadeada por hash que já existe | médio |
| Papéis (Architect, Auditor, Approver, **Epistemic Verifier**) e Amendment Protocol | **não é código: é processo.** O Approver humano é exigência do próprio Axioma X | — |

→ **2 a 3 sessões**, e não a incógnita que eu havia deixado em aberto.

**Onde o SLM entra de verdade.** O Reflection Core é uma pipeline de onze estados; o modelo local
não precisa ser brilhante, precisa ser um executor disciplinado dela, com o grafo ao lado. Isso é
RAG mais máquina de estados — não fine-tuning. E há um risco que a própria v3.0 documenta: um
modelo de 1–3B **vai** inventar proveniência se lhe deixarem. O gate JUSTIFY só protege se quem
verifica for código determinístico, não o próprio modelo se autodeclarando confiável. É a
diferença entre o LyraOS rodar e o LyraOS parecer que roda.

| | Esforço | Custo |
|---|---|---|
| **B total (com B4)** | **8 a 11 sessões** | R$ 0–500 (SSD opcional), + GPU só se quiser LoRA |

---

## O que um paga do outro

Terminar o GAEA **não é desviar** do LKF: é construir metade dele. O que já está pronto e migra
quase direto para o Diário:

- `servidor/config.py`, `seguranca.py`, `armazenamento.py` — configuração, senha, sessão,
  auditoria encadeada, retenção, backup verificado
- `servidor/gaea_api.py` — roteamento, CSRF, cabeçalhos, limitação de taxa, direitos LGPD
- `servidor/testes.py` — 36 controles que valem para qualquer app nosso
- `gaea_app.py` + `construir_exe.py` — janela, ícone, empacotamento em executável único

Chute honesto: **60 a 70% da fundação do B2 já está escrita**. Começar o LKF agora significa
escrever isso de novo com o GAEA parado a três sessões do fim.

---

## Recomendação

Fechar o GAEA — 2,5 a 3,5 sessões, uma delas dependendo só da VPS chegar — e emendar no LKF com
a fundação pronta e um executável que já sabemos gerar. É também o que a regra que combinamos
diz, e o motivo dela existir.

Resta uma pergunta: **que máquina vai rodar o SLM?** Com GPU de 8 GB ou mais, o LoRA entra no
cardápio; só com CPU, o desenho fica em RAG — que já entrega o que você descreveu.

## Achados na pasta LKF (para o dia em que o Diário nascer)

Dois problemas que qualquer ferramenta de texto — ou um SLM — vai encontrar antes de mim:

1. **Os `.MD` da raiz são DOCX renomeados.** `LKF Foundation Specification v1.0.MD`,
   `LyraOS Axioms.MD`, `TEST_CASE_001_FIRST_CONTACT.MD` e companhia abrem como ZIP, não como
   texto. Só consegui ler extraindo o `word/document.xml`. Os markdown de verdade estão em
   `LyraOSv2/LyraOS2/`.
2. **Há cópias divergentes do que a spec chama de fonte única de verdade:** `MAP.md` em três
   lugares, `LyraOS3.MD` em dois mais um `LyraOS3 - Copia.MD`. O Axioma V e o XII existem
   exatamente contra isso.

Isso não é crítica de arrumação: é o caso de uso número 1 do Diário. A primeira tarefa dele
deveria ser ingerir essa pasta, detectar duplicata por hash, marcar qual arquivo é canônico e
deprecar o resto — que é, literalmente, o LKF aplicado a si mesmo.
