#!/usr/bin/env python
"""
Oi eu sou o botinho do termo 🐬
"""
import asyncio
import time
from subprocess import run
from pyppeteer import launch
import pyperclip

TENTATIVA_INICIAL = "teias"
TAMANHO = len(TENTATIVA_INICIAL)


def procurar_palavras(comando, solucao):
    comando = ["python", "termo.py", comando]
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
        return proc.stdout.decode("utf-8").strip().split("\n")
    else:
        return None


async def main():
    print("Iniciando botinho")
    print()
    browser = await launch({"headless": False})
    # browser = await launch()
    page = await browser.newPage()
    await page.goto("https://term.ooo")
    fechar = await page.querySelector("#helpclose")
    await fechar.click()

    solucao = {
        "excluir": [],
        "fixar": [],
        "contem": [],
    }
    tentativa = TENTATIVA_INICIAL
    print("tentativa:", tentativa)
    for linha in range(1, 7):
        await page.keyboard.type(f"{tentativa}\n")
        time.sleep(TAMANHO)
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
            print(cell_class.removeprefix("letter "), tentativa[coluna - 1])

        if corretas == TAMANHO:
            print("Achou!")
            break
        print("Procurando palavras...")
        palavras = procurar_palavras("listar", solucao)
        if palavras is None:
            print(f"Oh no! Erro no comando")
            break
        elif len(palavras) == 0:
            print("Oh no! sem mais adivinhos")
            break

        print(f"Encontrou {len(palavras)} palavras. Mais provaveis: {palavras[:5]}")
        if len(palavras) == 1:
            tentativa = palavras[0]
        else:
            palavras_eliminar = procurar_palavras("eliminar", solucao)
            print(
                f"Encontrou {len(palavras_eliminar)} palavras ótimas. Melhores opções: {palavras_eliminar[:5]}"
            )
            if len(palavras_eliminar) < len(palavras):
                tentativa = palavras[0]
            else:
                tentativa = palavras_eliminar[0]

        print()
        print("tentativa:", tentativa)

    if corretas != TAMANHO:
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
