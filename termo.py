#!/usr/bin/env python
"""
Cansei de apanhar no termo.

➜ python termo.py -x e r t i p a l c n -f 2u 5o -c s
musgo
"""

from string import ascii_lowercase, digits
import argparse
from itertools import product
from collections import Counter
from os.path import isfile
from urllib.request import urlretrieve

WORDLIST = "wordlist.txt"


def baixar_wordlist():
    if not isfile(WORDLIST):
        print(f"Baixando lista de palavras para ${WORDLIST}")
        print("Isso só acontece uma vez hein")
        urlretrieve("https://www.ime.usp.br/~pf/dicios/br-sem-acentos.txt", WORDLIST)
        print("Pronto!")


def gerar_possibilidades(tamanho, excluir, fixar, contem):
    dicio = [l for l in list(ascii_lowercase) if l not in excluir]
    todas = [dicio for _ in range(tamanho)]
    for i, c in fixar.items():
        todas[i - 1] = [c]
    possibilidades = ["".join(p) for p in product(*todas)]
    possibilidades = [p for p in possibilidades if all([c[1] in p for c in contem])]
    possibilidades = [
        p for p in possibilidades if all([c[1] != p[c[0] - 1] for c in contem])
    ]
    return possibilidades


def listar_palavras(possibilidades):
    tamanho = len(possibilidades[0])
    with open(WORDLIST, "r") as fp:
        wordlist = set([w for w in fp.read().split() if len(w) == tamanho])
    palavras = set(possibilidades) & wordlist
    letras_freq = dict(Counter(",".join(palavras)))
    palavras = sorted(
        palavras, key=lambda palavra: -sum([letras_freq[l] for l in set(palavra)])
    )
    print("\n".join(palavras))


def tupla_numero_letra(strings):
    if (
        len(strings) != 2
        or strings[0] not in digits
        or strings[1] not in ascii_lowercase
    ):
        raise ArgumentError("Use a posição e a letra. Ex: (2o 3l)")
    return [int(strings[0]), strings[1]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pra jogar termo")
    parser.add_argument("-t", "--tamanho", type=int, default=5)
    parser.add_argument(
        "-x", "--excluir", nargs="+", default=list(), help="Letras que não tem"
    )
    parser.add_argument(
        "-f",
        "--fixar",
        nargs="+",
        type=tupla_numero_letra,
        help="Caracteres fixos (2o 3l)",
        default={},
    )
    parser.add_argument(
        "-c",
        "--contem",
        nargs="+",
        type=tupla_numero_letra,
        default=list(),
        help="Letras que tem (2o 3l)",
    )
    args = parser.parse_args()
    baixar_wordlist()
    possibilidades = gerar_possibilidades(
        args.tamanho, args.excluir, dict(args.fixar), args.contem
    )
    listar_palavras(possibilidades)
