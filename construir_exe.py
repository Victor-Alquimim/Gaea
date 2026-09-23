#!/usr/bin/env python3
r"""
GAEA · empacotador
==================

Gera um único GAEA.exe, sem Python instalado na máquina de destino.

    python -m pip install pyinstaller
    python construir_exe.py

Sai em dist/GAEA.exe (uns 12 MB). O executável carrega o app e o servidor
por dentro; os dados do usuário vão para %APPDATA%\GAEA — nunca para dentro
do .exe, que é somente leitura.

Antivírus costuma implicar com executável PyInstaller recém-nascido sem
assinatura. Para distribuir de verdade, assine com um certificado de code
signing; para uso próprio, basta liberar na primeira execução.
"""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SEP = ';' if sys.platform.startswith('win') else ':'


def main():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(__doc__)
        print('PyInstaller não está instalado. Rode:  python -m pip install pyinstaller')
        return 1

    if not (RAIZ / 'gaea.ico').exists():
        sys.path.insert(0, str(RAIZ / 'servidor'))
        import icone
        icone.escreve(RAIZ / 'gaea.ico')

    dados = ['index.html', 'css', 'js', 'data', 'gaea.ico', 'servidor']
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
           '--onefile', '--windowed', '--name', 'GAEA',
           '--icon', str(RAIZ / 'gaea.ico'),
           '--paths', str(RAIZ / 'servidor'),
           '--hidden-import', 'gaea_api', '--hidden-import', 'config',
           '--hidden-import', 'armazenamento', '--hidden-import', 'seguranca',
           '--hidden-import', 'icone']
    for d in dados:
        alvo = RAIZ / d
        if alvo.exists():
            cmd += ['--add-data', '%s%s%s' % (alvo, SEP, d if alvo.is_dir() else '.')]
    cmd.append(str(RAIZ / 'gaea_app.py'))

    print('empacotando…\n ' + ' '.join(cmd) + '\n')
    r = subprocess.run(cmd)
    if r.returncode == 0:
        print('\npronto: %s' % (RAIZ / 'dist' / 'GAEA.exe'))
    return r.returncode


if __name__ == '__main__':
    raise SystemExit(main())
