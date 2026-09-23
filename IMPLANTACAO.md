# GAEA · como colocar na rede

Quatro caminhos, do mais simples ao mais definitivo. Escolha pelo alcance que você precisa
hoje — dá para subir degrau depois sem reescrever nada.

| | Alcance | Custo | TLS | Quando usar |
|---|---|---|---|---|
| **1. Aplicativo** | só esta máquina | zero | não precisa | uso pessoal, demonstração |
| **2. Rede local** | mesmo wi-fi | zero | não | mostrar para a equipe, testar no celular |
| **3. Túnel** | internet | zero a baixo | sim, automático | publicar hoje sem servidor nem IP fixo |
| **4. Servidor** | internet | VPS a partir de ~US$5/mês | sim, automático | operação de verdade |

---

## 1. Aplicativo (clique duplo)

```
GAEA.cmd        ← clique duplo
```

Sobe o servidor dentro do próprio processo, abre o navegador e mostra uma janela com o
endereço, quantos macacos estão no mapa e onde ficam os dados. O botão **Criar atalho** põe
o GAEA na área de trabalho com ícone.

Para gerar um `.exe` que roda em máquina sem Python:

```bash
python -m pip install pyinstaller
python construir_exe.py            # sai em dist/GAEA.exe (~12 MB)
```

O executável guarda os dados em `%APPDATA%\GAEA` — o `.exe` em si é somente leitura.
Antivírus costuma implicar com binário PyInstaller sem assinatura; para distribuir a
terceiros, assine com certificado de *code signing*.

---

## 2. Rede local (o firewall pedindo passagem)

Na janela do app, marque **“Compartilhar na rede local”** — ou:

```bash
python gaea_app.py --rede
```

O servidor passa a escutar em `0.0.0.0` e **o Windows abre a caixa de diálogo do firewall**
pedindo autorização de rede. Autorize para redes privadas. A janela mostra o endereço de LAN
(algo como `http://192.168.1.33:5173/`) para abrir em qualquer celular ou notebook do mesmo
wi-fi.

Se a caixa não aparecer (ou você recusou antes), libere na mão, num PowerShell **como
administrador**:

```powershell
New-NetFirewallRule -DisplayName "GAEA" -Direction Inbound -Protocol TCP -LocalPort 5173 -Action Allow -Profile Private
```

Duas ressalvas honestas: esse tráfego é **HTTP puro**, sem cifra — use só em rede confiável; e
em `GAEA_MODO=dev` o mapa social aceita visitante sem login. Para qualquer coisa além de
demonstração interna, pule para o caminho 3 ou 4, que rodam em modo `producao`.

---

## 3. Túnel (internet hoje, sem abrir porta)

Um túnel publica o serviço que roda na sua máquina, com certificado válido, **sem** expor IP
nem mexer no roteador. Com Cloudflare Tunnel:

```bash
# 1) o GAEA em modo produção, escutando só em local
set GAEA_MODO=producao
set GAEA_ORIGEM=https://gaea.seudominio.com.br
set GAEA_TLS_BORDA=1
set GAEA_SEGREDO=<48 caracteres aleatórios>
python servidor/gaea_api.py

# 2) o túnel apontando para ele
cloudflared tunnel --url http://localhost:5173
```

A Cloudflare devolve um endereço `https://…`. Para endereço fixo, crie um túnel nomeado e
aponte seu domínio para ele. Ajuste `GAEA_ORIGEM` para o endereço definitivo: a checagem de
origem e o cookie `Secure` dependem disso.

Vale para demonstração e piloto. Não é o lugar de dado de produção sem antes fechar o
checklist da [SEGURANCA.md](SEGURANCA.md).

---

## 4. Servidor próprio (o jeito definitivo)

Uma VPS pequena (1 vCPU, 1 GB) aguenta o app com folga — ele é stdlib e o banco é um arquivo.

```bash
# na VPS, como root
adduser --system --group --home /opt/gaea gaea
mkdir -p /var/lib/gaea /etc/gaea && chown gaea:gaea /var/lib/gaea
git clone <seu-repo> /opt/gaea && chown -R gaea:gaea /opt/gaea

cp /opt/gaea/implantacao/gaea.env.exemplo /etc/gaea/gaea.env
chmod 600 /etc/gaea/gaea.env
python3 -c "import secrets;print('GAEA_SEGREDO='+secrets.token_urlsafe(48))" >> /etc/gaea/gaea.env
python3 -c "import secrets;print('GAEA_ADMIN_TOKEN='+secrets.token_urlsafe(32))" >> /etc/gaea/gaea.env
nano /etc/gaea/gaea.env          # ajuste GAEA_ORIGEM para o seu domínio

cp /opt/gaea/implantacao/gaea.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now gaea
systemctl status gaea            # deve dizer "modo producao"
```

TLS e proxy com Caddy (certificado automático, renovação automática):

```bash
cp /opt/gaea/Caddyfile /etc/caddy/Caddyfile
nano /etc/caddy/Caddyfile        # troque o domínio
systemctl reload caddy
```

Aponte o registro `A` do domínio para o IP da VPS e pronto. O `gaea.service` já roda com
`ProtectSystem=strict`, sem privilégios novos e com syscalls filtradas.

Backup diário, cifrado e com verificação:

```bash
cp /opt/gaea/implantacao/backup.sh /opt/gaea/implantacao/
crontab -e     #  15 3 * * *  /opt/gaea/implantacao/backup.sh
```

### Container, se preferir

```bash
docker build -t gaea .
docker run -d --name gaea -p 127.0.0.1:8080:8080 \
  -v gaea-dados:/dados \
  -e GAEA_SEGREDO="$(openssl rand -base64 36)" \
  -e GAEA_ORIGEM="https://gaea.seudominio.com.br" \
  -e GAEA_ADMIN_TOKEN="$(openssl rand -base64 24)" \
  gaea
```

A imagem roda como usuário sem privilégio, com o banco em volume e *healthcheck* batendo em
`/api/saude`. Serve igual em Fly.io, Render ou Railway — só passe as variáveis pelo painel de
segredos da plataforma, nunca no Dockerfile.

---

## Antes de apontar o DNS

```bash
python servidor/testes.py        # 36 controles, 0 falhas
curl -I https://seu-dominio/     # confira CSP, HSTS, X-Frame-Options
curl -H "X-GAEA-ADMIN: $GAEA_ADMIN_TOKEN" https://seu-dominio/api/admin/integridade
```

O restante do checklist — backup restaurado ao menos uma vez, alertas, política de
privacidade publicada, encarregado nomeado — está na [SEGURANCA.md](SEGURANCA.md), seção 7.

## Quanto aguenta

O gargalo real não é o GAEA: é a **Overpass API**, pública e com limite por IP. Com mais de um
punhado de usuários simultâneos, suba um cache seu (`overpass-api/db` em container) ou guarde
as consultas em disco com TTL de horas. O SQLite atende tranquilo até ~50 escritas por segundo;
acima disso, troque por Postgres — o esquema em `servidor/armazenamento.py` migra quase sem
alteração.
