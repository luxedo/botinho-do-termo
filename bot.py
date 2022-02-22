#!/usr/bin/env python
"""
Oi eu sou o botinho do termo 🐬
"""
from datetime import datetime
import random
import time
import pyperclip
from playwright.sync_api import sync_playwright

from termo import procurar, resolver

TAMANHO = 5


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


def main():
    print("Iniciando botinho")
    now = datetime.now()
    seed = int(f"9{now.day:02}{now.month:02}{now.year:04}")
    print(f"Semete randomica: {seed}\n")
    random.seed(seed)  # Make it reproductible *wink*

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("http://term.ooo")
        page.click("body")

        tentativas = []
        resultados = []
        linha = 1
        while linha < 7:
            resultado = ""
            print("Procurando palavras...")
            tentativa = resolver(tentativas, resultados, TAMANHO, verboso=True)
            if tentativa is None:
                print("Oh no! sem mais achados!")
                break
            print("tentativa:", tentativa)

            page.keyboard.type(f"{tentativa}\n")
            time.sleep(TAMANHO)
            for coluna in range(1, 6):
                cell = page.locator(
                    f"body > main > wc-board > wc-row:nth-child({linha+1}) > div:nth-child({coluna+1})"
                )
                cell_class = (
                    cell.get_attribute("class")
                    .removeprefix("letter ")
                    .removesuffix(" done")
                )
                resultado += cell_class[0]
            print(mostrar_bunito(tentativa, resultado))
            tentativas.append(tentativa)
            resultados.append(resultado)

            if cell_class == "empty":
                print("Oh no! Palavra invalida")
                for i in range(TAMANHO):
                    page.keyboard.press("Backspace")
                continue

            linha += 1
            todas_corretas = set(resultado) == set("r")
            if todas_corretas:
                print("Achou!")
                break

        if not todas_corretas:
            palavra = page.locator("body > wc-notify").inner_text().strip()
            if len(palavra) == TAMANHO:
                print(f"Não deu :( palavra '{palavra}' muito dificil")
            else:
                print("Estranho :(")
                print(palavra)
        compartilhar = page.locator("#stats_share")
        compartilhar.click()
        print(pyperclip.paste())

        browser.close()


if __name__ == "__main__":
    main()
