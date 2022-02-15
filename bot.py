#!/usr/bin/env python
"""
Oi eu sou o botinho do termo 🐬
"""
import asyncio
from datetime import datetime
import random
import time
from pyppeteer import launch
import pyperclip

from termo import procurar, resolver

TAMANHO = 5


async def main():
    print("Iniciando botinho")
    now = datetime.now()
    seed = int(f"9{now.day:02}{now.month:02}{now.year:04}")
    print(f"Semete randomica: {seed}")
    random.seed(seed)  # Make it reproductible *wink*
    print()

    browser = await launch({"headless": False})
    # browser = await launch()
    page = await browser.newPage()
    await page.goto("https://term.ooo")
    fechar = await page.querySelector("#help")
    await fechar.click()

    tentativas = []
    resultados = []
    linha = 1
    while linha < 7:
        resultado = ""
        print("Procurando palavras...")
        tentativa = resolver(tentativas, resultados, verboso=True)
        if tentativa is None:
            print("Oh no! sem mais achados!")
            break
        print("tentativa:", tentativa)

        await page.keyboard.type(f"{tentativa}\n")
        time.sleep(TAMANHO)
        for coluna in range(1, 6):
            cell = await page.querySelector(
                f"#board div:nth-child({linha}) div:nth-child({coluna})"
            )
            cell_class = (
                (await cell.getProperty("className"))
                .toString()
                .removeprefix("JSHandle:")
                .removeprefix("letter ")
                .removesuffix(" done")
            )
            resultado += cell_class[0]
            print(cell_class, tentativa[coluna - 1])
        tentativas.append(tentativa)
        resultados.append(resultado)

        if cell_class == "empty":
            print("Oh no! Palavra invalida")
            for i in range(TAMANHO):
                await page.keyboard.press("Backspace")
            continue

        linha += 1
        todas_corretas = set(resultado) == set("r")
        if todas_corretas:
            print("Achou!")
            break

    if not todas_corretas:
        palavra = (
            (await (await page.querySelector("#msg")).getProperty("innerHTML"))
            .toString()
            .removeprefix("JSHandle:")
        )
        if len(palavra) == TAMANHO:
            print(f"Não deu :( palavra '{palavra}' muito dificil")
        else:
            print("Estranho :(")
            print(palavra)
    compartilhar = await page.querySelector("#stats_share")
    await compartilhar.click()
    print(pyperclip.paste())
    await browser.close()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
