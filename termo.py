#!/usr/bin/env python
"""
Cansei de apanhar no termo.

# ➜ python termo.py procurar listar -x e r t i p a l c n -f 2u 5o -c 1s
# musgo

➜ python termo.py resolver -t teias -r rwwww -v
"""
import argparse
from collections import Counter
from dataclasses import dataclass
import math
import os
from os import path
import random
from string import ascii_lowercase, digits
from sys import stderr
from unidecode import unidecode

import numpy as np

LISTS_DIR = "dicionarios/"
WORDLIST = LISTS_DIR + "tf_{n}.txt"
WORDREPO = "pt-br/tf"
FREQUENCIA_MINIMA = 500
PALAVRAS_INICIAIS = 50
HEAD = "palavra |       tf | pesos | sl_tf | sl_pesos | prob"


cache_wordlist = None


@dataclass
class Palavra:
    palavra: str
    tf: int
    letras: set = None
    posicoes: set = None
    pesos: int = 0
    sf_tf: float = 0
    sf_pesos: float = 0
    prob: float = 0

    def __post_init__(self):
        self.letras = set(self.palavra)
        self.posicoes = set((i, l) for i, l in enumerate(self.palavra))

    def __str__(self):
        return f"{self.palavra:>7} | {self.tf:>8} | {self.pesos:>5} | {self.sf_tf:.03f} | {self.sf_pesos:.03f} | {self.prob:.03f}"


def carregar_wordlist(tamanho, frequencia_minima, processar):
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
                                if len(p) == tamanho and int(f) > frequencia_minima
                            ]
                        )
                    )
            print("Feito!", file=stderr)
        with open(WORDLIST.format(n=tamanho), "r") as fp:
            word_freq = [l.split(",") for l in fp.read().strip().split("\n")]
            cache_wordlist = [Palavra(w, int(f)) for w, f in word_freq]
    return cache_wordlist


def gerar_frequencias(possibilidades):
    repete_em_todas = set(ascii_lowercase).intersection(
        *[set(p.letras) for p in possibilidades]
    )
    return {
        key: value
        for key, value in dict(
            Counter("".join("".join(set(p.letras)) for p in possibilidades))
        ).items()
        if key not in repete_em_todas
    }


def filtrar_wordlist(
    wordlist,
    tamanho,
    excluir,
    fixar,
    contem,
    remover_palavras,
    talvez_contenha=set(),
    ord_freq=None,
):
    letras_contem = set(l[1] for l in contem)
    if talvez_contenha:
        possibilidades = [p for p in wordlist if talvez_contenha & p.letras != set()]
    else:
        possibilidades = wordlist
    possibilidades = [
        p
        for p in possibilidades
        if (p.posicoes & (excluir | contem) == set())
        and (p.posicoes & fixar == fixar)
        and (letras_contem - p.letras == set())
        and (p.palavra not in remover_palavras)
    ]

    if len(possibilidades) == 0:
        return None
    tamanho = len(possibilidades[0].palavra)
    if ord_freq is None:
        ord_freq = gerar_frequencias(possibilidades)

    for i, p in enumerate(possibilidades):
        p.pesos = sum(ord_freq.get(l, 0) for l in p.letras)

    exp_log_tf = np.exp(np.log([1 + p.tf for p in possibilidades]))
    exp_log_tf_sum = exp_log_tf.sum()
    exp_log_pesos = np.exp(np.log([1 + p.pesos for p in possibilidades]))
    exp_log_pesos_sum = exp_log_pesos.sum()
    for i, p in enumerate(possibilidades):
        p.sf_tf = exp_log_tf[i] / exp_log_tf_sum
        p.sf_pesos = exp_log_pesos[i] / exp_log_pesos_sum
        p.prob = p.sf_tf + p.sf_pesos

    exp_prob = np.exp([1 + p.prob for p in possibilidades])
    exp_prob_sum = exp_prob.sum()
    for i, p in enumerate(possibilidades):
        p.prob = exp_prob[i] / exp_prob_sum

    return sorted(possibilidades, key=lambda p: (-p.prob, -p.pesos))


def mostrar_palavras(possibilidades, mostrar_pesos, ordenar_tf):
    if ordenar_tf:
        possibilidades = sorted(possibilidades, key=lambda p: (-p.tf, -p.pesos))
    if mostrar_pesos:
        print(HEAD)
        for p in possibilidades:
            print(str(p))
    else:
        print("\n".join(p.palavra for p in possibilidades))


def procurar(
    comando, tamanho, processar, excluir, fixar, contem, remover_palavras=set()
):
    wordlist = carregar_wordlist(tamanho, FREQUENCIA_MINIMA, processar)
    possibilidades = filtrar_wordlist(
        wordlist, tamanho, excluir, fixar, contem, remover_palavras
    )

    if comando == "listar":
        return possibilidades

    elif comando == "eliminar":
        ord_freq = gerar_frequencias(possibilidades)
        possibilidades = filtrar_wordlist(
            wordlist,
            tamanho,
            excluir=set(),
            fixar=set(),
            contem=contem,
            remover_palavras=remover_palavras,
            talvez_contenha=set(ord_freq),
            ord_freq=ord_freq,
        )
        return possibilidades

    else:
        raise Exception("Algo está mto errado!")
        pass  # Num vai chegar aqui não

    return []


cache_palavras = None


def chute_inicial(tamanho):
    global cache_palavras
    if cache_palavras is None:
        cache_palavras = procurar(
            comando="eliminar",
            tamanho=tamanho,
            processar=False,
            excluir=set(),
            fixar=set(),
            contem=set(),
        )
    return random.choice(cache_palavras[:PALAVRAS_INICIAIS])


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
                        contem.add((i, letra))
                        continue
                for j in range(tamanho):
                    excluir.add((j, letra))
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
        tentativa = resolver(tentativas, resultados, len(palavra), verboso).palavra
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


def resolver(tentativas, resultados, tamanho, verboso=False):
    """
    Gera uma palavra para tentar resolver o term.ooo

    Args:
        tentativas (lista): lista de palavras
        resultados (lista): lista dos resultados de cada letra
            ('r' - right, 'w' - wrong, 'p' - place)
    """
    if verboso:
        print(f"resolver({tentativas}, {resultados}, verboso={verboso})")

    if len([r for r in resultados if r[0] != "e"]) == 0:
        return chute_inicial(tamanho)
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
        "remover_palavras": tentativas,
    }
    possibilidades = procurar("listar", **kwargs)

    if len(possibilidades) == 0:
        return None

    if verboso:
        print(
            f"Encontrou {len(possibilidades)} palavras. Mais provaveis:\n{HEAD}\n"
            + "\n".join(str(p) for p in possibilidades[:5]),
        )
    melhor_peso = sorted(possibilidades, key=lambda p: (-p.pesos, -p.tf))[0]
    melhor_tf = sorted(possibilidades, key=lambda p: (-p.tf, -p.pesos))[0]
    if melhor_tf.sf_tf > 0.9:
        return melhor_tf
    else:
        return melhor_peso
    # if possibilidades[0].tf > 0.9:
    #     return possibilidades[0]
    # else:
    #     return sorted(possibilidades, key=lambda p: (-p.pesos, -p.tf))[0]

    # else:
    #     palavras_eliminar = procurar("eliminar", **kwargs)
    #     palavras_eliminar = sorted(palavras_eliminar, key=lambda p: (-p.pesos, -p.tf))
    #     if len(palavras_eliminar) >= 1:
    #         return palavras_eliminar[0]
    #     else:
    #         return possibilidades[0]

    # encontradas = set(c[1] for c in contem)
    # if (
    #     (len(possibilidades) < 20 and max([p.sf_tf for p in possibilidades]) > 0.8)
    #     or linhas == 5
    #     or (len(fixar) <= 2 and len(encontradas) >= 3)
    # ):
    #     return possibilidades[0].palavra
    # else:
    #     palavras_eliminar = procurar("eliminar", **kwargs)
    #     palavras_eliminar = [p for p in palavras_eliminar if p not in tentativas]
    #     if verboso:
    #         print(
    #             f"Encontrou {len(palavras_eliminar)} palavras. Mais provaveis:\n{HEAD}\n"
    #             + "\n".join(str(p) for p in palavras_eliminar[:5]),
    #         )
    #     if len(palavras_eliminar) >= 1:
    #         return palavras_eliminar[0].palavra
    #     else:
    #         return possibilidades[0].palavra
    # return None  # Não deve chegar aqui hein


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
    subparsers = parser.add_subparsers(dest="comando", required=True)

    parser_resolver = subparsers.add_parser("resolver")
    parser_resolver.add_argument("-T", "--tamanho", type=int, default=5)
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

    parser_procurar.add_argument("-T", "--tamanho", type=int, default=5)
    parser_procurar.add_argument(
        "-x",
        "--excluir",
        nargs="+",
        type=tupla_numero_letra,
        default=set(),
        help="Letras que não tem",
    )
    parser_procurar.add_argument(
        "-f",
        "--fixar",
        nargs="+",
        type=tupla_numero_letra,
        default=set(),
        help="Caracteres fixos (2o 3l)",
    )
    parser_procurar.add_argument(
        "-c",
        "--contem",
        nargs="+",
        type=tupla_numero_letra,
        default=set(),
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
        possibilidades = procurar(
            args.comando_procurar[0],
            args.tamanho,
            args.processar,
            set(args.excluir),
            set(args.fixar),
            set(args.contem),
        )
        mostrar_palavras(possibilidades, args.mostrar_pesos, args.ordenar_tf)
    elif args.comando == "resolver":
        if len(args.tentativas) != len(args.resultados):
            raise ValueError("tentativas e resultados precisam ter o mesmo comprimento")
        tentativa = resolver(
            args.tentativas, args.resultados, args.tamanho, args.verboso
        )
        print()
        print(f"Melhor opção: {tentativa}")

    elif args.comando == "testar":
        rodadas = testar(args.palavra, args.verboso)
        if rodadas == 7:
            print("Não achou :(")
        else:
            print(f"Acertou em {rodadas}")
