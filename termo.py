#!/usr/bin/env python
"""
Cansei de apanhar no termo.

➜ python termo.py -x e r t i p a l c n -f 2u 5o -c s
musgo
"""
from string import ascii_lowercase, digits
import argparse
from collections import Counter
import math
import os
from os import path
import random
from sys import stderr
from unidecode import unidecode

LISTS_DIR = "dicionarios/"
WORDLIST = LISTS_DIR + "tf_{n}.txt"
WORDREPO = "pt-br/tf"
PALAVRAS_INICIAIS = 50


cache_wordlist = None


def carregar_wordlist(tamanho, processar):
    global cache_wordlist
    if cache_wordlist is None:
        if not path.isdir(LISTS_DIR):
            os.makedirs(LISTS_DIR)
        if not path.isfile(WORDLIST.format(n=tamanho)) or processar:
            print("Pré processando palavras... aguarde puvafô", file=stderr)
            print("Isso é feito apenas uma vez", file=stderr)
            with open(WORDLIST.format(n=tamanho), "w") as fw:
                with open(WORDREPO, "r") as fr:
                    dados = [l.split(",") for l in fr.read().strip().split("\n")]
                    fw.write(
                        "\n".join(
                            [
                                f"{unidecode(p)},{f}"
                                for p, f in dados
                                if len(p) == 5 and int(f) > 0
                            ]
                        )
                    )
            print("Feito!", file=stderr)
        with open(WORDLIST.format(n=tamanho), "r") as fp:
            cache_wordlist, freqs = zip(
                *[l.split(",") for l in fp.read().strip().split("\n")]
            )
            cache_wordlist = list(
                zip(
                    cache_wordlist,
                    list(map(set, cache_wordlist)),
                    list(
                        map(
                            lambda palavra: set((i, l) for i, l in enumerate(palavra)),
                            cache_wordlist,
                        )
                    ),
                    [int(f) for f in freqs],
                )
            )
    return cache_wordlist


def calcular_peso(palavra, ord_freq):
    letras = set(palavra)
    return sum([ord_freq.get(l, 0) for l in letras])


def log_softmax(dados):
    xp = [math.exp(math.log(x + 1)) for x in dados]
    soma = sum(xp)
    return [x / soma for x in xp]


def log_softmax_coluna(achados, coluna):
    transposto = list(zip(*achados))
    transposto[coluna] = log_softmax(transposto[coluna])
    return list(zip(*transposto))


def gerar_frequencias(achados):
    repete_em_todas = set(ascii_lowercase).intersection(*[set(a[0]) for a in achados])
    return {
        key: value
        for key, value in dict(
            Counter("".join(["".join(set(a[0])) for a in achados]))
        ).items()
        if key not in repete_em_todas
    }


def filtrar_wordlist(
    wordlist,
    tamanho,
    excluir,
    fixar,
    contem,
    talvez_contenha=set(),
    ord_freq=None,
):
    contem = set([c for c in contem if all(c[1] != f[1] for f in fixar)])
    letras_contem = set(c[1] for c in contem)
    possibilidades = [
        (p, f)
        for p, sw, sp, f in wordlist
        if (not sw & excluir)
        and ((fixar & sp) == fixar)
        and (not letras_contem - sw)
        and (not contem & sp)
        and (len(talvez_contenha) == 0 or sw & talvez_contenha)
    ]

    if len(possibilidades) == 0:
        return []
    tamanho = len(possibilidades[0])
    if ord_freq is None:
        ord_freq = gerar_frequencias(possibilidades)
    achados = map(lambda p: [p[0], calcular_peso(p[0], ord_freq), p[1]], possibilidades)
    achados = log_softmax_coluna(achados, 1)
    return sorted(achados, key=lambda row: (row[2], row[1]), reverse=True)


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
    achados = filtrar_wordlist(wordlist, tamanho, excluir, fixar, contem)

    if comando == "listar":
        return achados

    elif comando == "eliminar":
        ord_freq = gerar_frequencias(achados)
        achados = filtrar_wordlist(
            wordlist,
            tamanho,
            excluir=set(),
            fixar=set(),
            contem=set(),
            talvez_contenha=set(ord_freq),
            ord_freq=ord_freq,
        )
        return achados

    else:
        raise Exception("Algo está mto errado!")
        pass  # Num vai chegar aqui não

    return []


cache_palavras = None


def chute_inicial():
    global cache_palavras
    if cache_palavras is None:
        cache_palavras = procurar(
            comando="eliminar",
            tamanho=5,
            processar=False,
            excluir=set(),
            fixar=set(),
            contem=set(),
        )
    return random.choice(cache_palavras[:PALAVRAS_INICIAIS])[0]


def gerar_argumentos(tentativas, resultados):
    if len(tentativas) == 0:
        return set(), set(), set()
    tamanho = len(tentativas[0])
    excluir = set()
    fixar = set()
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
                fixar.add((i, letra))
            elif res == "e":
                pass  # ignorar palavras que nao existem no dicio
            else:
                raise ValueError("Resultado so pode ter 'r', 'w', ou 'p'")
    return excluir, fixar, contem


def testar(palavra, verboso):
    tentativas = []
    resultados = []
    for i in range(1, 7):
        tentativa = resolver(tentativas, resultados, verboso)
        resultado = ""
        for l, t in zip(palavra, tentativa):
            if l == t:
                resultado += "r"
            elif t in palavra:
                resultado += "p"
            else:
                resultado += "w"
        resultados.append(resultado)
        tentativas.append(tentativa)
        if set(resultado) == set("r"):
            return i
    return 7


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
    linhas = len([r for r in resultados if r[0] != "e"])
    processar = not path.isfile(WORDLIST.format(n=tamanho))
    kwargs = {
        "tamanho": tamanho,
        "processar": processar,
        "excluir": excluir,
        "fixar": fixar,
        "contem": contem,
    }
    achados = procurar("listar", **kwargs)
    achados = [a for a in achados if a[0] not in tentativas]
    if len(achados) == 0:
        return None

    achados = sorted(achados, key=lambda x: (x[1], x[2]), reverse=True)
    if verboso:
        mais_provaveis = "\n".join(
            [f"{a[0]} - {a[1]:03f} - {a[2]:.3f}" for a in achados[:5]]
        )
        print(f"Encontrou {len(achados)} palavras. Mais provaveis:\n{mais_provaveis}")

    encontradas = set(c[1] for c in contem)
    if (
        (len(achados) < 20 and achados[0][1] > 0.8)
        or linhas == 5
        or (len(fixar) <= 2 and len(encontradas) >= 3)
    ):
        return achados[0][0]
    else:
        palavras_eliminar = procurar("eliminar", **kwargs)
        palavras_eliminar = [a for a in achados if a[0] not in tentativas]
        if verboso:
            mais_provaveis = "\n".join(
                [f"{a[0]} - {a[1]:03f} - {a[2]:.3f}" for a in palavras_eliminar[:5]]
            )
            print(
                f"Encontrou {len(palavras_eliminar)} palavras. Otimas:\n{mais_provaveis}"
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

    parser_testar = subparsers.add_parser("testar")
    parser_testar.add_argument("palavra")
    parser_testar.add_argument("-v", "--verboso", action="store_true")

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
            set(args.excluir),
            set(args.fixar),
            set(args.contem),
        )
        mostrar_palavras(achados, args.mostrar_pesos, args.ordenar_tf)
    elif args.comando == "resolver":
        if len(args.tentativas) != len(args.resultados):
            raise ValueError("tentativas e resultados precisam ter o mesmo comprimento")
        tentativa = resolver(args.tentativas, args.resultados, args.verboso)
        print()
        print(f"Melhor opção: {tentativa}")

    elif args.comando == "testar":
        rodadas = testar(args.palavra, args.verboso)
        if rodadas == 7:
            print("Não achou :(")
        else:
            print(f"Acertou em {rodadas}")
