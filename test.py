import random
import time

import termo

TAMANHO = 5
RODADAS = 1000
# RODADAS = 10


def simular_jogo(palavra):
    tentativas = []
    resultados = []
    for i in range(1, 7):
        tentativa = termo.resolver(tentativas, resultados, TAMANHO)
        resultado = ""
        for l, t in zip(palavra, tentativa.palavra):
            if l == t:
                resultado += "r"
            elif t in palavra:
                resultado += "p"
            else:
                resultado += "w"
        resultados.append(resultado)
        tentativas.append(tentativa.palavra)
        if set(resultado) == set("r"):
            return i
        # if tentativa is None:
        #     return 6
    return 7


def testar(rodadas):
    t0 = time.time()
    wordlist = termo.carregar_wordlist(TAMANHO, termo.FREQUENCIA_MINIMA, False)
    wordlist = [p for p in wordlist if p.tf > 10000]
    acertos = []
    t1 = time.time()
    for i in range(rodadas):
        palavra = random.choice(wordlist).palavra
        acertos.append(simular_jogo(palavra))
    tf = time.time()
    print("Média de acertos")
    print(sum(acertos) / len(acertos))
    print(f"Overhead (s): {t1-t0:.02f}")
    print(f"Tempo total (s): {tf-t1:.02f}")
    print(f"Tempo por iter (ms): {(tf-t1)/RODADAS * 1000:.02f}")


if __name__ == "__main__":
    testar(RODADAS)
