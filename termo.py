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
import math
import os
from os import path
import sys
from unidecode import unidecode

LISTS_DIR = "dicionarios/"
WORDLIST = LISTS_DIR + "wordlist_{n}.txt"
TFLIST = LISTS_DIR + "tf_{n}.csv"
WORDREPO = "pt-br/palavras"
TFREPO = "pt-br/tf"
FREQUENCIAS = "eitsanhurdmwgvlfbkopjxczyq"
VOGAIS = "eiauo"


def carregar_wordlist(tamanho, forcar):
    if not path.isdir(LISTS_DIR):
        os.makedirs(LISTS_DIR)
    if not path.isfile(WORDLIST.format(n=tamanho)) or forcar:
        print("Pré processando palavras... aguarde puvafô", file=sys.stderr)
        print("Isso é feito apenas uma vez", file=sys.stderr)
        with open(WORDLIST.format(n=tamanho), "w") as fw:
            with open(WORDREPO, "r") as fr:
                fw.write(
                    "\n".join(
                        [
                            unidecode(l)
                            for l in fr.read().split("\n")
                            if len(l) == tamanho
                        ]
                    )
                )
        print("Feito!", file=sys.stderr)
    with open(WORDLIST.format(n=tamanho), "r") as fp:
        return fp.read().strip().split("\n")


def carregar_tf(tamanho, forcar):
    if not path.isdir(LISTS_DIR):
        os.makedirs(LISTS_DIR)
    if not path.isfile(TFLIST.format(n=tamanho)) or forcar:
        print(
            "Pré processando frequencias das palavras... aguarde puvafô",
            file=sys.stderr,
        )
        print("Isso é feito apenas uma vez", file=sys.stderr)
        with open(TFLIST.format(n=tamanho), "w") as fw:
            with open(TFREPO, "r") as fr:
                palavras = [l.split(",") for l in fr.read().split("\n")]
                palavras = [
                    f"{unidecode(p[0])},{p[1]}"
                    for p in palavras
                    if len(p[0]) == tamanho
                ]
                fw.write("\n".join(palavras))
        print("Feito!", file=sys.stderr)
    with open(TFLIST.format(n=tamanho), "r") as fp:
        return dict(
            map(
                lambda p: (p[0], int(p[1])),
                [t.split(",") for t in fp.read().strip().split("\n")],
            )
        )


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


def calcular_peso(palavra, ord_freq, tf):
    letras = set(palavra)
    return (
        palavra,
        tf.get(palavra),
        sum(
            [
                (
                    ord_freq.get(l, 0)
                    + FREQUENCIAS[::-1].index(l) / len(FREQUENCIAS) / len(letras)
                )
                for l in letras
            ]
        ),
    )


def log_softmax(dados):
    xp = [math.exp(math.log(x + 1)) for x in dados]
    soma = sum(xp)
    return [x / soma for x in xp]


def log_softmax_coluna(achados, coluna):
    transposto = list(zip(*achados))
    transposto[coluna] = log_softmax(transposto[coluna])
    return list(zip(*transposto))


def listar_palavras(possibilidades, wordlist, tf, ord_freq=None):
    if len(possibilidades) == 0:
        return []
    tamanho = len(possibilidades[0])
    palavras = set(possibilidades) & set(wordlist)
    if len(palavras) == 0:
        return []
    if ord_freq is None:
        ord_freq = dict(Counter("".join(palavras)))
    achados = map(lambda p: calcular_peso(p, ord_freq, tf), palavras)
    achados = log_softmax_coluna(achados, 1)
    return sorted(achados, key=lambda row: -row[2])


def tupla_numero_letra(strings):
    if (
        len(strings) != 2
        or strings[0] not in digits
        or strings[1] not in ascii_lowercase
    ):
        raise ValueError("Use a posição e a letra. Ex: (2o 3l)")
    return [int(strings[0]), strings[1]]


def mostrar_palavras(achados, mostrar_pesos, ordenar_tf):
    print(
        "\n".join(
            [
                f"{p[0]} - {p[1]:.03f} - {p[2]:.03f}" if mostrar_pesos else p[0]
                for p in (
                    achados
                    if not ordenar_tf
                    else sorted(achados, key=lambda row: -row[1])
                )
            ]
        )
    )


def main(args):
    wordlist = carregar_wordlist(args.tamanho, args.processar)
    tf = carregar_tf(args.tamanho, args.processar)
    possibilidades = gerar_possibilidades(
        args.tamanho, args.excluir, dict(args.fixar), args.contem, []
    )
    achados = list(listar_palavras(possibilidades, wordlist, tf))

    if args.comando[0] == "listar":
        mostrar_palavras(achados, args.mostrar_pesos, args.ordenar_tf)

    elif args.comando[0] == "eliminar":
        # 1. Tenta gerar palavras com todas as letras restantes
        ord_freq = dict(Counter("".join([p[0] for p in achados])))
        letras_usadas = list(
            set(
                list(args.excluir)
                + [f[1] for f in args.fixar]
                + [c[1] for c in args.contem]
            )
        )
        possibilidades = gerar_possibilidades(
            args.tamanho, excluir=letras_usadas, fixar={}, contem={}, talvez_contenha=[]
        )
        achados = listar_palavras(possibilidades, wordlist, tf, ord_freq)
        if len(achados) != 0:
            mostrar_palavras(achados, args.mostrar_pesos, args.ordenar_tf)
            return

        # 2. Remove letras da lista de exclusões por ordem de frequencia reversa
        for c in reversed(ord_freq):
            if c in letras_usadas:
                letras_usadas_vogal = letras_usadas[:]
                letras_usadas_vogal.remove(c)
                possibilidades = gerar_possibilidades(
                    args.tamanho,
                    excluir=letras_usadas_vogal,
                    fixar={},
                    contem={},
                    talvez_contenha=list(ord_freq),
                )
                achados = listar_palavras(possibilidades, wordlist, tf, ord_freq)
                if len(achados) != 0:
                    mostrar_palavras(achados, args.mostrar_pesos, args.ordenar_tf)
                    return

        # 3. Ainda não pensei

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
    parser.add_argument(
        "-o",
        "--ordenar-tf",
        action="store_true",
        help="Ordena pela frequencia das palavras",
    )
    parser.add_argument(
        "-m",
        "--mostrar-pesos",
        action="store_true",
        help="Mostra os pesos calculados para cada palavra",
    )
    args = parser.parse_args()
    main(args)
