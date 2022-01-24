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
import os
from os import path
from unidecode import unidecode

WORDLIST = "wordlist_{n}.txt"
WORDREPO = "pt-br/palavras"
FREQUENCIAS = "eitsanhurdmwgvlfbkopjxczyq"


def processar_wordlist(tamanho, forcar):
    if not path.isfile(WORDLIST.format(n=tamanho)) or forcar:
        print("Pré processando palavras... aguarde puvafô")
        print("Isso é feito apenas uma vez")
        with open(WORDLIST.format(n=tamanho), "w") as fw:
            with open("pt-br/palavras", "r") as fr:
                fw.write(
                    "\n".join(
                        [
                            unidecode(l)
                            for l in fr.read().split("\n")
                            if len(l) == tamanho
                        ]
                    )
                )
        print("Feito!")


def gerar_possibilidades(tamanho, excluir, fixar, contem, talvez_contenha):
    dicio = [l for l in list(ascii_lowercase) if l not in excluir]
    todas = [dicio for _ in range(tamanho)]
    for i, c in fixar.items():
        todas[i - 1] = [c]
    possibilidades = ["".join(p) for p in product(*todas)]
    possibilidades = [p for p in possibilidades if all([c[1] in p for c in contem])]
    possibilidades = [
        p for p in possibilidades if all([c[1] != p[c[0] - 1] for c in contem])
    ]
    if talvez_contenha:
        possibilidades = [
            p for p in possibilidades if any([t in p for t in talvez_contenha])
        ]
    return possibilidades


def listar_palavras(possibilidades, frequencias_ord=FREQUENCIAS):
    tamanho = len(possibilidades[0])
    with open(WORDLIST.format(n=tamanho), "r") as fp:
        wordlist = set([w for w in fp.read().split() if len(w) == tamanho])
    palavras = set(possibilidades) & wordlist
    letras_freq = dict(Counter(",".join(palavras)))
    palavras = sorted(
        palavras,
        key=lambda palavra: -sum(
            [
                len(ascii_lowercase) * letras_freq[l] + frequencias_ord[::-1].find(l)
                for l in set(palavra)
            ]
        ),
    )
    return palavras


def tupla_numero_letra(strings):
    if (
        len(strings) != 2
        or strings[0] not in digits
        or strings[1] not in ascii_lowercase
    ):
        raise ValueError("Use a posição e a letra. Ex: (2o 3l)")
    return [int(strings[0]), strings[1]]


def main(args):
    processar_wordlist(args.tamanho, args.processar)
    possibilidades = gerar_possibilidades(
        args.tamanho, args.excluir, dict(args.fixar), args.contem, []
    )
    palavras = listar_palavras(possibilidades)
    if args.comando[0] == "listar":
        print("\n".join(palavras))
    elif args.comando[0] == "eliminar":
        # print(Counter("".join(palavras)).most_common())
        # 1. Tenta gerar palavras com todas as letras restantes
        contador = Counter("".join(palavras))
        frequencias_ord = "".join(contador)
        letras_usadas = (
            list(args.excluir)
            + [f[1] for f in args.fixar]
            + [c[1] for c in args.contem]
        )
        possibilidades = gerar_possibilidades(
            args.tamanho, excluir=letras_usadas, fixar={}, contem={}, talvez_contenha=[]
        )
        palavras = listar_palavras(possibilidades, frequencias_ord)
        if len(palavras) != 0:
            print("\n".join(palavras))
            return

        # 2. Elimina uma consoantes por ordem de frequencia reversa
        for c in reversed(frequencias_ord):
            if c in letras_usadas:
                letras_usadas_vogal = letras_usadas[:]
                letras_usadas_vogal.remove(c)
                possibilidades = gerar_possibilidades(
                    args.tamanho,
                    excluir=letras_usadas_vogal,
                    fixar={},
                    contem={},
                    talvez_contenha=list(frequencias_ord),
                )
                palavras = listar_palavras(possibilidades, frequencias_ord)
                if len(palavras) != 0:
                    print("\n".join(palavras))
                    return

        # 3. Tenta gerar palavras com todas as letras restantes adicionando vogais eliminadas
        for v in "ouaie":
            if v in letras_usadas:
                letras_usadas_vogal = letras_usadas[:]
                letras_usadas_vogal.remove(v)
                possibilidades = gerar_possibilidades(
                    args.tamanho,
                    excluir=letras_usadas_vogal,
                    fixar={},
                    contem={},
                    talvez_contenha=list(frequencias_ord),
                )
                palavras = listar_palavras(possibilidades, frequencias_ord)
                if len(palavras) != 0:
                    print("\n".join(palavras))
                    return

        # 4. Ainda não pensei

    else:
        raise Exception("Algo está mto errado!")
        pass  # Num vai chegar aqui não


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pra jogar termo")
    parser.add_argument(
        "comando",
        choices=["listar", "eliminar"],
        nargs=1,
        help="Lista palavras ou determina a palavra que maximiza a eliminação de letras.",
    )
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
    parser.add_argument(
        "-p",
        "--processar",
        action="store_true",
        help="Realiza o processamento do dicionário",
    )
    args = parser.parse_args()
    main(args)
