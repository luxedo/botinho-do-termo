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
import random
from sys import stderr
from unidecode import unidecode

LISTS_DIR = "dicionarios/"
WORDLIST = LISTS_DIR + "wordlist_{n}.txt"
TFLIST = LISTS_DIR + "tf_{n}.csv"
WORDREPO = "pt-br/palavras"
TFREPO = "pt-br/tf"
PALAVRAS_INICIAIS = 50


def carregar_wordlist(tamanho, processar):
    if not path.isdir(LISTS_DIR):
        os.makedirs(LISTS_DIR)
    if not path.isfile(WORDLIST.format(n=tamanho)) or processar:
        print("Pré processando palavras... aguarde puvafô", file=stderr)
        print("Isso é feito apenas uma vez", file=stderr)
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
        print("Feito!", file=stderr)
    with open(WORDLIST.format(n=tamanho), "r") as fp:
        return fp.read().strip().split("\n")


def carregar_tf(tamanho, processar):
    if not path.isdir(LISTS_DIR):
        os.makedirs(LISTS_DIR)
    if not path.isfile(TFLIST.format(n=tamanho)) or processar:
        print(
            "Pré processando frequencias das palavras... aguarde puvafô",
            file=stderr,
        )
        print("Isso é feito apenas uma vez", file=stderr)
        with open(TFLIST.format(n=tamanho), "w") as fw:
            with open(TFREPO, "r") as fr:
                palavras = [l.split(",") for l in fr.read().split("\n")]
                palavras = [
                    f"{unidecode(p[0])},{p[1]}"
                    for p in palavras
                    if len(p[0]) == tamanho
                ]
                fw.write("\n".join(palavras))
        print("Feito!", file=stderr)
    with open(TFLIST.format(n=tamanho), "r") as fp:
        return dict(
            map(
                lambda p: (p[0], int(p[1])),
                [t.split(",") for t in fp.read().strip().split("\n")],
            )
        )


def calcular_peso(palavra, ord_freq, tf, lf):
    letras = set(palavra)
    return (
        palavra,
        tf.get(palavra),
        sum(
            [
                (ord_freq.get(l, 0) + lf[::-1].index(l) / len(lf) / len(letras))
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


def filtrar_wordlist(
    wordlist,
    tf,
    lf,
    tamanho,
    excluir,
    fixar,
    contem,
    talvez_contenha=None,
    ord_freq=None,
):
    possibilidades = [p for p in wordlist if not any(l in p for l in excluir)]
    possibilidades = [
        p for p in possibilidades if all(f == p[i] for i, f in fixar.items())
    ]
    possibilidades = [p for p in possibilidades if all(c in p for i, c in contem)]
    possibilidades = [p for p in possibilidades if all(c != p[i] for i, c in contem)]
    if talvez_contenha:
        achados = [p for p in possibilidades if any([t in p for t in talvez_contenha])]

    if len(possibilidades) == 0:
        return []
    tamanho = len(possibilidades[0])
    if ord_freq is None:
        ord_freq = dict(Counter("".join(possibilidades)))
    achados = map(lambda p: calcular_peso(p, ord_freq, tf, lf), possibilidades)
    achados = log_softmax_coluna(achados, 1)
    return sorted(achados, key=lambda row: (row[2], row[0]), reverse=True)


def mostrar_palavras(achados, mostrar_pesos, ordenar_tf):
    print(
        "\n".join(
            [
                f"{p[0]} - {p[1]:.03f} - {p[2]:.03f}" if mostrar_pesos else p[0]
                for p in (
                    achados
                    if not ordenar_tf
                    else sorted(achados, key=lambda row: (row[1], row[0]), reverse=True)
                )
            ]
        )
    )


def procurar(
    comando,
    tamanho,
    processar,
    excluir,
    fixar,
    contem,
):
    wordlist = carregar_wordlist(tamanho, processar)
    tf = carregar_tf(tamanho, processar)
    lf = "".join(
        [
            f[0]
            for f in sorted(
                Counter("".join(wordlist)).most_common(), key=lambda x: -x[1]
            )
        ]
    )
    achados = filtrar_wordlist(wordlist, tf, lf, tamanho, excluir, fixar, contem)

    if comando == "listar":
        return achados

    elif comando == "eliminar":
        repete_em_todas = set(ascii_lowercase).intersection(
            *[set(a[0]) for a in achados]
        )
        ord_freq = {
            key: value
            for key, value in dict(
                Counter("".join(["".join(set(a[0])) for a in achados]))
            ).items()
            if key not in repete_em_todas
        }
        achados = filtrar_wordlist(
            wordlist,
            tf,
            lf,
            tamanho,
            excluir=[],
            fixar={},
            contem={},
            talvez_contenha=list(ord_freq),
            ord_freq=ord_freq,
        )
        return achados

    else:
        raise Exception("Algo está mto errado!")
        pass  # Num vai chegar aqui não

    return []


def chute_inicial():
    palavras = procurar(
        comando="eliminar", tamanho=5, processar=False, excluir=[], fixar={}, contem=[]
    )
    return random.choice(palavras[:PALAVRAS_INICIAIS])[0]


def gerar_argumentos(tentativas, resultados):
    if len(tentativas) == 0:
        return [], {}, []
    tamanho = len(tentativas[0])
    excluir = set()
    fixar = {}
    contem = set()
    for palavra, resultado in zip(tentativas, resultados):
        duplicadas = [l for l in palavra if palavra.count(l) > 1]
        for i, (letra, res) in enumerate(zip(palavra, resultado)):
            if res == "w":
                if letra in duplicadas:
                    conflitos = [
                        resultado[i] for i in range(tamanho) if letra == palavra[i]
                    ]
                    if set(conflitos) != set("w"):
                        continue
                excluir.add(letra)
            elif res == "p":
                contem.add((i, letra))
            elif res == "r":
                fixar[i] = letra
            else:
                raise ValueError("Resultado so pode ter 'r', 'w', ou 'p'")
    return excluir, fixar, contem


def resolver(tentativas, resultados, verboso=False):
    """
    Gera uma palavra para tentar resolver o term.ooo

    Args:
        tentativas (lista): lista de palavras
        resultados (lista): lista dos resultados de cada letra
            ('r' - right, 'w' - wrong, 'p' - place)
    """
    if verboso:
        print(f"resolver({tentativas}, {resultados}, verboso={verboso})")

    if len(tentativas) == 0:
        return chute_inicial()
    excluir, fixar, contem = gerar_argumentos(tentativas, resultados)

    if verboso:
        print(f"excluir: {excluir}")
        print(f"fixar: {fixar}")
        print(f"contem: {contem}")

    tamanho = len(tentativas[0])
    linhas = len(tentativas)
    processar = not path.isfile(WORDLIST.format(n=tamanho))
    kwargs = {
        "tamanho": tamanho,
        "processar": processar,
        "excluir": excluir,
        "fixar": fixar,
        "contem": contem,
    }
    achados = procurar("listar", **kwargs)
    if len(achados) == 0:
        return None

    achados = sorted(achados, key=lambda x: (x[1], x[0]), reverse=True)
    if verboso:
        mais_provaveis = "\n".join(
            [f"{a[0]} - {a[1]:03f} - {a[2]:.3f}" for a in achados[:5]]
        )
        print(f"Encontrou {len(achados)} palavras. Mais provaveis:\n{mais_provaveis}")

    encontradas = set(c[1] for c in contem)
    if (
        (len(achados) < 5 and achados[0][1] > 0.8)
        or linhas == 5
        or (len(fixar) <= 2 and len(encontradas) >= 3)
    ):
        return achados[0][0]
    else:
        palavras_eliminar = procurar("eliminar", **kwargs)
        if verboso:
            mais_provaveis = "\n".join(
                [f"{a[0]} - {a[1]:03f} - {a[2]:.3f}" for a in palavras_eliminar[:5]]
            )
            print(
                f"Encontrou {len(palavras_eliminar)} palavras. Mais provaveis:\n{mais_provaveis}"
            )
        if len(palavras_eliminar) >= 1:
            return palavras_eliminar[0][0]
        else:
            return achados[0][0]

    return None  # Não deve chegar aqui hein


def tupla_numero_letra(strings):
    if (
        len(strings) != 2
        or strings[0] not in digits
        or strings[1] not in ascii_lowercase
    ):
        raise ValueError("Use a posição e a letra. Ex: (2o 3l)")
    return int(strings[0]) - 1, strings[1]  # Indexando a partir de 1 pq sim


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pra jogar termo")
    subparsers = parser.add_subparsers(dest="comando")

    parser_resolver = subparsers.add_parser("resolver")
    parser_resolver.add_argument("-t", "--tentativas", nargs="*")
    parser_resolver.add_argument("-r", "--resultados", nargs="*")
    parser_resolver.add_argument("-v", "--verboso", action="store_true")

    parser_procurar = subparsers.add_parser("procurar")
    parser_procurar.add_argument(
        "comando_procurar",
        choices=["listar", "eliminar"],
        nargs=1,
        help="Lista palavras ou determina a palavra que maximiza a eliminação de letras.",
    )

    parser_procurar.add_argument("-t", "--tamanho", type=int, default=5)
    parser_procurar.add_argument(
        "-x", "--excluir", nargs="+", default=list(), help="Letras que não tem"
    )
    parser_procurar.add_argument(
        "-f",
        "--fixar",
        nargs="+",
        type=tupla_numero_letra,
        help="Caracteres fixos (2o 3l)",
        default={},
    )
    parser_procurar.add_argument(
        "-c",
        "--contem",
        nargs="+",
        type=tupla_numero_letra,
        default=list(),
        help="Letras que tem (2o 3l)",
    )
    parser_procurar.add_argument(
        "-p",
        "--processar",
        action="store_true",
        help="Realiza o processamento do dicionário",
    )
    parser_procurar.add_argument(
        "-o",
        "--ordenar-tf",
        action="store_true",
        help="Ordena pela frequencia das palavras",
    )
    parser_procurar.add_argument(
        "-m",
        "--mostrar-pesos",
        action="store_true",
        help="Mostra os pesos calculados para cada palavra",
    )
    args = parser.parse_args()
    if args.comando in "procurar":
        achados = procurar(
            args.comando_procurar[0],
            args.tamanho,
            args.processar,
            args.excluir,
            dict(args.fixar),
            args.contem,
        )
        mostrar_palavras(achados, args.mostrar_pesos, args.ordenar_tf)
    elif args.comando == "resolver":
        if len(args.tentativas) != len(args.resultados):
            raise ValueError("tentativas e resultados precisam ter o mesmo comprimento")
        tentativa = resolver(args.tentativas, args.resultados, args.verboso)
        print()
        print(f"Melhor opção: {tentativa}")
