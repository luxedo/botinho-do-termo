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

from termo import procurar

TAMANHO = 5
PALAVRAS_INICIAIS = 50


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
    fechar = await page.querySelector("#helpclose")
    await fechar.click()

    kwargs = {
        "excluir": set(),
        "fixar": {},
        "contem": [],
        "tamanho": TAMANHO,
        "processar": False,
    }
    letras = set()
    palavras = procurar(comando="eliminar", **kwargs)
    tentativa = random.choice(palavras[:PALAVRAS_INICIAIS])[0]
    print("tentativa:", tentativa)
    for linha in range(1, 7):
        await page.keyboard.type(f"{tentativa}\n")
        time.sleep(TAMANHO)
        respostas = set()
        for coluna in range(1, 6):
            letra = tentativa[coluna - 1]
            cell = await page.querySelector(
                f"#board div:nth-child({linha}) div:nth-child({coluna})"
            )
            cell_value = (
                (await cell.getProperty("innerHTML"))
                .toString()
                .removeprefix("JSHandle:")
            )
            cell_class = (
                (await cell.getProperty("className"))
                .toString()
                .removeprefix("JSHandle:")
                .removeprefix("letter ")
                .removesuffix(" done")
            )
            respostas.add((coluna, letra, cell_class))
            print(cell_class, tentativa[coluna - 1])

        todas_corretas = all(c == "right" for _, _, c in list(respostas))
        if todas_corretas:
            print("Achou!")
            break

        duplicadas = [l for l in tentativa if tentativa.count(l) > 1]
        for (coluna, letra, cell_class) in list(respostas):
            if cell_class == "wrong":
                if letra in duplicadas:
                    conflitos = [c for c in list(respostas) if c[1] == letra]
                    if not all(c[2] == "wrong" for c in conflitos):
                        continue
                kwargs["excluir"].add(tentativa[coluna - 1])
            elif cell_class == "place":
                kwargs["contem"].append([coluna, tentativa[coluna - 1]])
                letras.add(tentativa[coluna - 1])
            elif cell_class == "right":
                kwargs["fixar"][coluna] = tentativa[coluna - 1]
                letras.add(tentativa[coluna - 1])
            else:
                print("no!", cell_value, cell_class)

        print("Procurando palavras...")
        print("listar", kwargs)
        achados = procurar(comando="listar", **kwargs)
        if len(achados) == 0:
            print("Oh no! sem mais adivinhos")
            break

        achados = sorted(achados, key=lambda x: (x[1], x[0]), reverse=True)
        mais_provaveis = "\n".join(
            [f"{a[0]} - {a[1]:03f} - {a[2]:.3f}" for a in achados[:5]]
        )
        print(f"Encontrou {len(achados)} palavras. Mais provaveis:\n{mais_provaveis}")
        if (
            (len(achados) < 5 and achados[0][1] > 0.8)
            or linha == 6
            or (len(kwargs["fixar"]) == 0 and len(letras) > 3)
        ):
            tentativa = achados[0][0]
        else:
            print("eliminar", kwargs)
            palavras_eliminar = procurar(comando="eliminar", **kwargs)
            if len(palavras_eliminar) >= 1:
                mais_provaveis = "\n".join(
                    [f"{a[0]} - {a[1]:03f} - {a[2]:.3f}" for a in palavras_eliminar[:5]]
                )
                print(
                    f"Encontrou {len(palavras_eliminar)} palavras. Ótimas:\n{mais_provaveis}"
                )
                tentativa = palavras_eliminar[0][0]
            else:
                tentativa = achados[0][0]

        print()
        print("tentativa:", tentativa)

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
