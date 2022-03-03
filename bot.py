#!/usr/bin/env python
"""
Oi eu sou o botinho do termo 🐬
"""
from datetime import datetime
import random
import subprocess
import time
from playwright.sync_api import sync_playwright

from termo import procurar, resolver

TAMANHO = 5


def copiar_clipboard(primary=False, mime=None):
    selection = "c"
    if primary:
        selection = "p"
    command = ["xclip", "-selection", selection, "-o"]
    if mime is not None:
        command += ["-t", mime]
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )
    stdout, stderr = p.communicate()
    # Intentionally ignore extraneous output on stderr when clipboard is empty
    if mime is None:
        return stdout.decode("utf-8")
    else:
        return stdout


def mostrar_bunito(tentativa, resultado):
    bunito_map = {
        "w": "⬛",
        "p": "🟨",
        "r": "🟩",
        "e": "⬜",
    }
    return (
        " "
        + " ".join(tentativa)
        + "\n"
        + "".join(bunito_map.get(r, " ") for r in resultado)
    )


def resolver_termo(url, imagem=False):
    print(f"Resolvendo: {url}")
    now = datetime.now()
    seed = int(f"9{now.day:02}{now.month:02}{now.year:04}")
    print(f"Semete randomica: {seed}\n")
    random.seed(seed)  # Make it reproductible *wink*

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.click("body")

        linhas = page.locator(f"main > wc-board:first-child > #hold > wc-row").count()
        boards = page.locator(f"wc-board").count()
        print(f"linhas: {linhas},colunas: {boards}")
        resolvidas = [False for _ in range(boards)]
        tentativas = [list() for _ in range(boards)]
        resultados = [list() for _ in range(boards)]
        linha = 1
        while linha <= linhas:
            print("Procurando palavras...")
            chutes = [
                resolver(tentativas[t], resultados[t], TAMANHO, verboso=True)
                for t in range(boards)
                if not resolvidas[t]
            ]
            chutes = [c for c in chutes if c is not None]
            if len(chutes) == 0:
                print("Oh no! sem mais achados!")
                break

            tentativa = sorted(chutes, key=lambda x: -x.prob)[0]
            print("tentativa:", tentativa)

            page.keyboard.type(f"{tentativa.palavra}\n")
            time.sleep(TAMANHO)
            for board in range(boards):
                if resolvidas[board]:
                    continue
                resultado = ""
                for coluna in range(1, TAMANHO + 1):
                    cell = page.locator(
                        f"main > wc-board:nth-child({board + 1}) > #hold > wc-row:nth-child({linha}) > div:nth-child({coluna+1})"
                    )
                    cell_class = (
                        cell.get_attribute("class")
                        .removeprefix("letter ")
                        .removesuffix(" done")
                    )
                    resultado += cell_class[0]
                print(mostrar_bunito(tentativa.palavra, resultado))
                tentativas[board].append(tentativa.palavra)
                resultados[board].append(resultado)

            if cell_class == "empty":
                print("Oh no! Palavra invalida")
                for i in range(TAMANHO):
                    page.keyboard.press("Backspace")
                continue

            linha += 1
            resolvidas = [set(r[-1]) == set("r") for r in resultados]
            if all(resolvidas):
                print("Achou!")
                break

        if not all(resolvidas):
            palavra = page.locator("body > wc-notify").inner_text().strip()
            if len(palavra) == TAMANHO:
                print(f"Não deu :( palavra '{palavra}' muito dificil")
            else:
                print("Estranho :(")
                print(palavra)
        compartilhar = page.locator("#stats_share")
        if imagem:
            compartilhar.click()
            img = copiar_clipboard(mime="image/png")
            with open("dia.png", "wb") as fp:
                fp.write(img)
            time.sleep(10)
        compartilhar.click()
        paste = copiar_clipboard()
        browser.close()
        return paste


if __name__ == "__main__":
    print("Iniciando botinho")
    termo1 = resolver_termo("http://term.ooo")
    termo2 = resolver_termo("http://term.ooo/2")
    termo4 = resolver_termo("http://term.ooo/4", imagem=True)
    print(termo1)
    print(termo2)
    print(termo4)
