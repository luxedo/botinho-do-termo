#!/usr/bin/env python
"""
Oi eu sou o botinho do termo 🐬
"""
import asyncio
import time
from subprocess import run
from pyppeteer import launch
import pyperclip
import termo

TENTATIVA_INICIAL = "teias"


async def main():
    browser = await launch({"headless": False})
    page = await browser.newPage()
    await page.goto("https://term.ooo")
    fechar = await page.querySelector("#helpclose")
    await fechar.click()

    i = 1
    solucao = {
        "excluir": [],
        "fixar": [],
        "contem": [],
    }
    tentativa = TENTATIVA_INICIAL
    for linha in range(1, 7):
        await page.keyboard.type(f"{tentativa}\n")
        time.sleep(5)
        corretas = 0
        for coluna in range(1, 6):
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
            )
            if "wrong" in cell_class:
                solucao["excluir"].append(f"{tentativa[coluna-1]}")
            elif "place" in cell_class:
                solucao["contem"].append(f"{coluna}{tentativa[coluna-1]}")
            elif "right" in cell_class:
                solucao["fixar"].append(f"{coluna}{tentativa[coluna-1]}")
                corretas += 1
            else:
                print("no!", cell_value, cell_class)
            print(cell_value, cell_class, tentativa[coluna - 1])
        comando = ["python", "termo.py"]
        if len(solucao["excluir"]) > 0:
            comando += ["--excluir"] + list(set(solucao["excluir"]))
        if len(solucao["fixar"]) > 0:
            comando += ["--fixar"] + list(set(solucao["fixar"]))
        if len(solucao["contem"]) > 0:
            fixas = set([f[1] for f in solucao["fixar"]])
            contem = list(set([c for c in solucao["contem"] if c[1] not in fixas]))
            if len(contem) > 0:
                comando += ["--contem"] + contem
        print(" ".join(comando))
        proc = run(comando, capture_output=True)
        if proc.returncode == 0:
            tentativa = proc.stdout.split(b"\n")[0].decode("utf-8")
            print("tentativa:", tentativa)
            if len(tentativa) == 0:
                print("Oh no! sem mais adivinhos")
                tentativa = "errou"
            elif corretas == 5:
                print("Achou!")
                break
        else:
            print(f"Oh no! Erro no comando")
            break

    if corretas != 5:
        palavra = (
            (await (await page.querySelector("#msg")).getProperty("innerHTML"))
            .toString()
            .removeprefix("JSHandle:")
        )
        if len(palavra) == 5:
            print(f"Não deu :( adicionando '{palavra}' ao dicionario")
            with open(termo.WORDLIST, "a") as fp:
                fp.write(palavra)
        else:
            print("Estranho :(")
            print(palavra)
    compartilhar = await page.querySelector("#stats_share")
    await compartilhar.click()
    print(pyperclip.paste())
    await browser.close()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
