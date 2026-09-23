#!/usr/bin/env python3
"""
GAEA · aplicativo
=================

Clique duplo e o mapa abre: este arquivo sobe o servidor dentro do próprio
processo, abre o navegador e mostra uma janelinha com o estado do serviço.

    python gaea_app.py              # janela (ou console, se não houver tkinter)
    python gaea_app.py --rede       # já começa compartilhando na rede local
    python gaea_app.py --console    # sem janela, só terminal

Compartilhar na rede local faz o servidor escutar em todas as interfaces
(0.0.0.0). É nesse momento que o Windows pergunta se o GAEA pode acessar a
rede — é o firewall do sistema pedindo sua autorização, e vale para a rede
local. Publicar na internet é outro assunto: veja IMPLANTACAO.md.
"""

import os
import socket
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

# congelado, os arquivos vivem na pasta temporária do bundle
if getattr(sys, 'frozen', False):
    AQUI = Path(getattr(sys, '_MEIPASS', Path(sys.executable).resolve().parent))
    EXECUTAVEL = Path(sys.executable).resolve()
else:
    AQUI = Path(__file__).resolve().parent
    EXECUTAVEL = AQUI / 'GAEA.cmd'
sys.path.insert(0, str(AQUI / 'servidor'))

PORTA_PADRAO = int(os.environ.get('GAEA_PORTA', 5173))
ABRE_NAVEGADOR = os.environ.get('GAEA_SEM_NAVEGADOR', '').strip().lower() not in ('1', 'true', 'sim')


def abre(url):
    if ABRE_NAVEGADOR:
        webbrowser.open(url)


def porta_livre(preferida):
    for p in [preferida] + list(range(preferida + 1, preferida + 20)):
        s = socket.socket()
        try:
            s.bind(('127.0.0.1', p))
            return p
        except OSError:
            continue
        finally:
            s.close()
    return preferida


def ip_local():
    """IP da máquina na rede local, sem depender de DNS nem de internet."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))     # não envia nada; só resolve a rota
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()


class Servico:
    """Sobe e derruba o servidor HTTP dentro deste processo."""

    def __init__(self, porta):
        self.porta = porta
        os.environ.setdefault('GAEA_PORTA', str(porta))
        from http.server import ThreadingHTTPServer
        import gaea_api
        from config import config
        self._ThreadingHTTPServer = ThreadingHTTPServer
        self.api = gaea_api
        self.config = config
        self.config.porta = porta
        self.config.origem = 'http://localhost:%d' % porta
        self.srv = None
        self.host = '127.0.0.1'
        threading.Thread(target=self.api.zelador, daemon=True).start()

    def sobe(self, host):
        self.derruba()
        self.host = host
        self.config.host = host
        self.srv = self._ThreadingHTTPServer((host, self.porta), self.api.App)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.api.banco.audita('servico.subiu', None, 'app host=%s' % host, '')

    def derruba(self):
        if self.srv:
            self.srv.shutdown()
            self.srv.server_close()
            self.srv = None

    @property
    def url(self):
        return 'http://localhost:%d/' % self.porta

    @property
    def url_rede(self):
        return 'http://%s:%d/' % (ip_local(), self.porta)

    def online(self):
        try:
            return self.api.banco.conta_presencas(self.config.retencao_presenca_seg)
        except Exception:
            return 0


def atalho_area_de_trabalho():
    """Cria o atalho no desktop via WScript.Shell (só Windows)."""
    if os.name != 'nt':
        return 'atalho automático só no Windows'
    alvo = EXECUTAVEL
    icone = EXECUTAVEL if getattr(sys, 'frozen', False) else (AQUI / 'gaea.ico')
    ps = (
        "$s=(New-Object -ComObject WScript.Shell);"
        "$l=$s.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\\GAEA.lnk');"
        "$l.TargetPath='%s';$l.WorkingDirectory='%s';$l.IconLocation='%s';"
        "$l.Description='GAEA - mapa de fluxo e espacos abertos';$l.Save()"
    ) % (alvo, alvo.parent, icone)
    try:
        subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', ps],
                       check=True, capture_output=True, timeout=30)
        return 'atalho criado na área de trabalho'
    except Exception as e:
        return 'não consegui criar o atalho (%s)' % type(e).__name__


# ─────────────────────────── janela ───────────────────────────
def janela(servico, comecar_na_rede):
    import tkinter as tk
    from tkinter import font as tkfont
    from icone import SPRITE, CORES, escreve

    PAPEL, TINTA, VERDE, CINZA = '#f4f1ea', '#16221f', '#1f7a5c', '#7d908a'
    raiz = tk.Tk()
    raiz.title('GAEA')
    raiz.configure(bg=PAPEL)
    raiz.geometry('460x372')
    raiz.resizable(False, False)
    try:
        ico = AQUI / 'gaea.ico'
        if not ico.exists():
            escreve(ico)
        raiz.iconbitmap(str(ico))
    except Exception:
        pass

    titulo = tkfont.Font(family='Segoe UI', size=17, weight='bold')
    corpo = tkfont.Font(family='Segoe UI', size=9)
    mono = tkfont.Font(family='Consolas', size=9)

    topo = tk.Frame(raiz, bg=PAPEL)
    topo.pack(fill='x', padx=18, pady=(16, 8))

    lado = 5
    cv = tk.Canvas(topo, width=16 * lado, height=16 * lado, bg=PAPEL, highlightthickness=0)
    cv.pack(side='left')
    for y, linha in enumerate(SPRITE):
        for x, ch in enumerate(linha):
            r, g, b, a = CORES[ch]
            if a:
                cv.create_rectangle(x * lado, y * lado, (x + 1) * lado, (y + 1) * lado,
                                    fill='#%02x%02x%02x' % (r, g, b), outline='')

    texto = tk.Frame(topo, bg=PAPEL)
    texto.pack(side='left', padx=12)
    tk.Label(texto, text='GAEA', font=titulo, bg=PAPEL, fg=TINTA).pack(anchor='w')
    tk.Label(texto, text='fluxo de massas · espaços abertos', font=corpo,
             bg=PAPEL, fg=CINZA).pack(anchor='w')

    estado = tk.Label(raiz, text='subindo o servidor…', font=corpo, bg=PAPEL, fg=TINTA)
    estado.pack(anchor='w', padx=18)
    endereco = tk.Label(raiz, text='', font=mono, bg=PAPEL, fg=VERDE, cursor='hand2')
    endereco.pack(anchor='w', padx=18, pady=(2, 8))

    na_rede = tk.BooleanVar(value=comecar_na_rede)
    aviso = tk.Label(raiz, text='', font=corpo, bg=PAPEL, fg='#a9761f',
                     wraplength=420, justify='left')

    def aplica(*_):
        host = '0.0.0.0' if na_rede.get() else '127.0.0.1'
        try:
            servico.sobe(host)
        except OSError as e:
            estado.config(text='não consegui escutar em %s (%s)' % (host, e))
            return
        if na_rede.get():
            estado.config(text='no ar · visível na rede local')
            endereco.config(text=servico.url_rede)
            aviso.config(text='O Windows pode pedir autorização de rede agora — é o firewall '
                              'perguntando se o GAEA pode aceitar conexões. Vale para a rede local: '
                              'quem estiver no mesmo wi-fi abre pelo endereço acima. Em modo dev o '
                              'mapa social aceita visitante sem login; para internet, veja IMPLANTACAO.md.')
        else:
            estado.config(text='no ar · só nesta máquina')
            endereco.config(text=servico.url)
            aviso.config(text='')
        aviso.pack(anchor='w', padx=18, pady=(0, 4))

    endereco.bind('<Button-1>', lambda e: abre(endereco.cget('text')))

    tk.Checkbutton(raiz, text='Compartilhar na rede local (pede acesso ao firewall)',
                   variable=na_rede, command=aplica, bg=PAPEL, fg=TINTA, font=corpo,
                   activebackground=PAPEL, selectcolor=PAPEL,
                   highlightthickness=0, bd=0).pack(anchor='w', padx=14)

    botoes = tk.Frame(raiz, bg=PAPEL)
    botoes.pack(fill='x', padx=18, pady=10)

    def botao(pai, texto_b, cmd, destaque=False):
        b = tk.Button(pai, text=texto_b, command=cmd, font=corpo, bd=0, padx=12, pady=6,
                      bg=VERDE if destaque else '#ffffff', fg='#ffffff' if destaque else TINTA,
                      activebackground=VERDE if destaque else '#eceadf',
                      activeforeground='#ffffff' if destaque else TINTA, cursor='hand2')
        b.pack(side='left', padx=(0, 8))
        return b

    botao(botoes, 'Abrir no navegador', lambda: webbrowser.open(endereco.cget('text')), True)
    botao(botoes, 'Criar atalho', lambda: estado.config(text=atalho_area_de_trabalho()))
    botao(botoes, 'Sair', lambda: fechar())

    rodape = tk.Label(raiz, text='', font=corpo, bg=PAPEL, fg=CINZA, justify='left')
    rodape.pack(anchor='w', padx=18, pady=(2, 0))

    def pulso():
        try:
            n = servico.online()
            rodape.config(text='macacos no mapa agora: %d   ·   dados em %s'
                               % (n, servico.config.banco))
        except Exception:
            pass
        raiz.after(5000, pulso)

    def fechar():
        servico.derruba()
        raiz.destroy()

    raiz.protocol('WM_DELETE_WINDOW', fechar)
    aplica()
    pulso()
    raiz.after(400, lambda: abre(endereco.cget('text')))
    raiz.mainloop()


# ─────────────────────────── console ───────────────────────────
def console(servico, na_rede):
    servico.sobe('0.0.0.0' if na_rede else '127.0.0.1')
    print('GAEA no ar em %s' % (servico.url_rede if na_rede else servico.url))
    if na_rede:
        print('escutando em todas as interfaces — o firewall do sistema pode pedir autorização')
    print('Ctrl+C para parar')
    abre(servico.url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        servico.derruba()
        print('\nencerrado')


def main():
    args = sys.argv[1:]
    na_rede = '--rede' in args
    servico = Servico(porta_livre(PORTA_PADRAO))
    if '--console' in args:
        return console(servico, na_rede)
    try:
        janela(servico, na_rede)
    except Exception as e:                      # sem tkinter, sem drama
        print('janela indisponível (%s); caindo para o modo console' % type(e).__name__)
        console(servico, na_rede)


if __name__ == '__main__':
    main()
