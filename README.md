# GAEA · fluxo de massas + espaços abertos

Mapa web que cruza **espaços públicos abertos** (parques, praças, áreas verdes, orlas de
cursos d'água e represas, spots de permanência) com o **fluxo de movimentação de pessoas**
ao longo do dia, num desenho esquemático — relevo suave por baixo, cores chapadas por cima,
no espírito das camadas do Google Maps.

## Rodar

**Clique duplo em `GAEA.cmd`** — sobe o servidor, abre o navegador e mostra uma janela com o
endereço, os macacos online e um interruptor para compartilhar na rede local (é ele que faz o
Windows pedir a autorização de firewall). Para gerar um `.exe` sem Python na máquina de
destino: `python -m pip install pyinstaller && python construir_exe.py`.

Pela linha de comando:

```bash
python gaea_app.py            # aplicativo com janela
python gaea_app.py --rede     # já compartilhando na rede local
python servidor/gaea_api.py   # só o servidor, sem janela
```

Para publicar na internet — túnel, VPS com TLS automático ou container — veja
[IMPLANTACAO.md](IMPLANTACAO.md).

Abra `http://localhost:5173`. Não há build nem dependência instalada: é HTML/CSS/JS puro,
com Leaflet e leaflet.heat vindos de CDN. O servidor é stdlib do Python e faz três coisas: serve os arquivos, expõe a API (conta,
pins, presença) e aplica os controles de segurança descritos em [SEGURANCA.md](SEGURANCA.md).
Os dados ficam num SQLite em `servidor/dados/` (fora do versionamento).

```bash
python servidor/testes.py     # 36 verificações de controle, com o número ISO ao lado
```

## O que vem de onde

| Camada | Fonte |
|---|---|
| Lugares (geometria + nome + tags) | **OpenStreetMap** via **Overpass API** (3 espelhos com timeout e failover) |
| Base esquemática e rótulos | **CARTO** (voyager / light, tiles derivados do OSM) |
| Relevo | **OpenTopoMap**, em `multiply` sobre a base, com opacidade regulável |
| Busca de endereço/cidade | **Nominatim** |
| Fotos do local | **Wikimedia Commons** (geosearch por raio em torno do centroide) |
| Street View / Maps | links diretos para o Google (`map_action=pano`) |
| Fluxo de pessoas | **modelo sintético** (ver abaixo), **trajetos GPS do OSM** ou arquivo seu |
| Satélite de hoje | **NASA GIBS** (VIIRS/MODIS, WMTS) · **Esri World Imagery** · **RainViewer** |

## O modelo de fluxo — leia isto

O app **não tem base real de localização de usuários conectada**. O que ele desenha por
padrão é um modelo sintético e determinístico, calculado assim:

1. cada lugar vira um **nó** com peso = categoria × tamanho × ter nome próprio;
2. nós a menos de 3,2 km trocam fluxo, com volume ∝ `peso_a × peso_b / distância` —
   os 130 pares mais fortes viram **corredores**;
3. a **hora do dia** modula tudo por uma curva por categoria (parque tem pico de manhã e
   no fim da tarde; praça tem pico no almoço e à noite; há curva separada para fim de semana);
4. o resultado alimenta três representações: mapa de calor, partículas correndo pelos
   corredores e círculos de hotspot dimensionados pela intensidade.

Os números em "pessoas/h" são, portanto, **estimativas do modelo**, não medições. Servem para
comparar lugares e horários entre si, não para citar como contagem real.

### Usar dados reais

Três caminhos, do mais rápido ao mais trabalhoso:

1. **Assistente → OpenStreetMap · trajetos GPS públicos → "Importar traces desta área".**
   Movimento humano real, com horário, sem chave e sem cadastro. O app baixa os trackpoints
   do enquadramento atual, agrega numa grade de ~55 m por hora e passa a usá-los como fonte.
2. **Assistente → Seus dados**, que lista o que estiver registrado em `data/index.json`.
3. **Fluxo de movimentação → importar dados reais**, para um arquivo avulso do seu disco:
   **CSV** com `lat`, `lon` e, opcionalmente, `hora` (0–23) e `peso`; ou **GeoJSON** de pontos.

Com fonte real ligada, a unidade na interface muda de *pessoas/h* (estimativa do modelo) para
*registros/h* (contagem do que foi medido) — o app não finge que ping é pessoa. O botão
*Baixar CSV do último import* gera o arquivo já no formato de `data/`.

## A pasta `data/`

```
data/
├── index.json          catálogo que o app lista no assistente
├── osm-traces-sjrp.csv 3.371 células de trajetos GPS reais de São José do Rio Preto (ODbL)
├── pings-exemplo.csv   1.494 pings sintéticos de Campo Grande, para testar o pipeline
├── brutos/             o que você baixou, antes de padronizar
└── README.md           esquema das colunas e nota de privacidade
```

## Avatar

Cada perfil desenha o próprio macaco num sprite 24×24 de `<rect>` ([js/avatar.js](js/avatar.js)):
pelo (7 cores), focinho (4), colete (6), fundo (6), olhar (normais, felizes, óculos, esperto)
e cabeça (boné, palha, folha, fones, coroa). O editor fica na tela do perfil, com preview de
104 px e botão de sortear. O mesmo avatar aparece no chip da barra lateral, nos seus pins e
no mapa social — e continua se coçando e pulando como o macaco original.

## Mapa social

Ligar o mapa social publica **apelido, avatar e uma posição** no servidor de presença e mostra
quem mais está online. Antes de qualquer coisa acontecer, uma tela lista exatamente o que sai
do navegador e pede a precisão:

| Precisão | Arredondamento | O que dá para saber de você |
|---|---|---|
| Exata | nenhum | onde você está, com erro de GPS |
| Aproximada *(padrão)* | ~500 m | a quadra, não a casa |
| Bairro | ~2 km | a região, só isso |

Não vai e-mail, não vai senha, não vai histórico de trajeto — só a última posição. O servidor
guarda em memória, descarta depois de **5 minutos** sem notícia, e *Sair do mapa* apaga o
registro na hora (inclusive ao fechar a aba, via `sendBeacon`). O log do servidor é escrito sem
query string de propósito, para coordenada nenhuma cair em disco.

**Alcance:** o servidor é local. Enxergam-se quem estiver na mesma máquina ou na mesma rede.
Não existe serviço público do GAEA na internet — para valer entre cidades, este processo
precisa rodar num host que as duas pontas alcancem.

Para ver a coisa em pé sem duas máquinas:

```bash
python servidor/macacos_demo.py -20.8113 -49.3758 4
```

Os macacos de teste entram com “(demo)” no apelido e somem sozinhos em 5 minutos.

## Perfis e planos

O GAEA não tem servidor: o perfil é **local**, guardado no `localStorage` deste navegador
(senha só como hash SHA-256 — separa perfis na mesma máquina, não protege disco de ninguém).
Cada perfil carrega seu plano, seu cofre de chaves e seus pins.

| | Free | Pro |
|---|---|---|
| Mapa esquemático, relevo, camadas de lugar | ✓ | ✓ |
| Modelo de fluxo do segundo ao dia inteiro | ✓ | ✓ |
| Ficha com fotos do Commons e Street View | ✓ | ✓ |
| Pins do macaco | ✓ | ✓ |
| Avatar e mapa social | ✓ | ✓ |
| Assistente de dados (catálogo de fontes) | — | ✓ |
| Camadas de satélite de hoje, radar, alta resolução | — | ✓ |
| Importar fluxo real (traces OSM, FIRMS, CSV, GeoJSON) | — | ✓ |
| Cofre de chaves de API com teste de validade | — | ✓ |
| Exportar pings importados em CSV | — | ✓ |

A ativação do Pro é um interruptor local, sem cobrança e sem cadastro externo — o app não
tem para onde mandar pagamento nem a quem cobrar.

### Sobre criar contas nos provedores automaticamente

O app **não** cria conta em serviço de terceiro no seu nome, e isso não é limitação técnica:
abrir conta, aceitar termos e passar por verificação são atos seus, e automatizar isso viola
os termos de Google, NASA, OpenWeather e MapTiler. O que dava para automatizar está feito —
cada cartão abre a página exata do cadastro, traz o passo a passo, e o botão **Testar** faz
uma chamada real ao provedor para dizer na hora se a chave funciona antes de você salvá-la.

## Pins do macaco

Botão **Pin do macaco** liga o modo; cada clique no mapa larga um macaco de 16×16 pixels
desenhado na paleta da casa (ocre da praça, papel, tinta, o laranja do fluxo no colete). Ele
se coça sem parar e dá um pulo a cada ~6 s. O pin é arrastável, aceita nome e anotação, tem
atalho para o Street View e fica salvo no perfil. Quem pediu `prefers-reduced-motion` recebe
o macaco parado.

## Assistente de dados

O botão **Dados & satélite** abre um painel que lê o enquadramento atual (faz geocodificação
reversa para dizer onde você está), sugere os três próximos passos e lista o catálogo de fontes
gratuitas em quatro grupos — satélite, tempo real, fluxo de pessoas e território. Cada cartão
diz o que a fonte entrega, com que frequência atualiza, sob que licença, e se precisa de chave.

Ligam na hora, **sem nenhuma chave**: VIIRS cor real de hoje, MODIS cor real de hoje, falsa cor
de hoje, luzes noturnas de ontem, anomalias térmicas de hoje (todos NASA GIBS), Esri World
Imagery de alta resolução e o radar de chuva do RainViewer.

## Chaves de API

As chaves ficam **só no `localStorage` do seu navegador** — o GAEA não tem servidor e nunca as
envia para lugar nenhum; as chamadas saem do seu navegador direto para o provedor. Cada cartão
que pede chave traz o passo a passo e o link da página onde ela é emitida:

| Chave | Para quê | Custo |
|---|---|---|
| Google Maps | foto de Street View dentro da ficha do local | crédito mensal grátis, exige cartão |
| NASA FIRMS `MAP_KEY` | focos de calor das últimas 24 h como pings | grátis, só e-mail |
| OpenWeather | tiles de precipitação/nuvem/vento | grátis até 60 chamadas/min |
| MapTiler | base de satélite alternativa | grátis até 100k tiles/mês |

Nada além disso é obrigatório: o app inteiro funciona sem uma única chave.

## Uso

- **Buscar nesta área** consulta o Overpass no enquadramento atual (zoom ≥ 11).
- A linha do tempo cobre o dia inteiro **em segundos** (0–86399). O seletor `h · min · seg`
  muda o passo do arrasto e do play; o relógio mostra `HH:MM` ou `HH:MM:SS` conforme o passo,
  e **agora** salta para o horário atual.
- Entre os pontos horários das curvas o valor é interpolado (Catmull-Rom com volta à
  meia-noite) e recebe um pulso curto, determinístico e defasado por lugar — é o que faz
  um minuto diferir do seguinte em vez de a tela congelar entre horas cheias.
- Com pings reais, a leitura usa uma janela de ±30 min em torno do instante escolhido.
- ▶ anima o dia inteiro; o seletor troca dia útil / fim de semana.
- Clique em qualquer polígono, linha ou hotspot para abrir a ficha com fotos, métricas,
  curva do dia e os links de Street View / Maps / OSM.
- As camadas de lugar e de fluxo ligam e desligam individualmente; preferências e último
  enquadramento ficam no `localStorage`.

## Arquivos

```
index.html        estrutura e painéis
css/style.css     design tokens, tema claro/escuro, responsivo
js/config.js      paleta, categorias OSM, curvas horárias, consulta Overpass
js/osm.js         Overpass, Nominatim, Commons, geometria (área/centroide)
js/flow.js        modelo de fluxo, índice espacial dos pings, partículas em canvas
js/catalogo.js    catálogo de fontes, chaves de API, importadores (traces OSM, FIRMS)
js/agente.js      painel do assistente: contexto, sugestões, cartões, formulário de chave
js/avatar.js      sprite 24×24 do macaco e editor de avatar
js/contas.js      perfis locais, planos Free/Pro, portão dos recursos extras
js/presenca.js    consentimento, compartilhamento de posição e mapa social
js/pins.js        o macaco 16-bit, modo de marcação, editor e lista
js/app.js         estado, mapa, camadas, ficha, controles
data/             seus CSV de fluxo real
servidor/         app + API: gaea_api.py, config.py, seguranca.py, armazenamento.py, testes.py
gaea_app.py       aplicativo de janela (tkinter) que sobe o servidor e abre o mapa
GAEA.cmd          atalho de clique duplo · construir_exe.py gera dist/GAEA.exe
implantacao/      systemd, variáveis de ambiente e backup cifrado · Dockerfile · Caddyfile
```

No console, `GAEA.map`, `GAEA.flow`, `GAEA.estado` e `GAEA.carregar()` estão expostos para inspeção.
