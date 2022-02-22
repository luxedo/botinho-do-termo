import random
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
        # if tentativa is None:
        #     return 6
    return 7


def testar():
    wordlist = termo.carregar_wordlist(TAMANHO, termo.FREQUENCIA_MINIMA, False)
    wordlist = [p for p in wordlist if p.tf > 10000]
    acertos = []
    for i in range(RODADAS):
        palavra = random.choice(wordlist).palavra
        acertos.append(simular_jogo(palavra))
    print("Média de acertos")
    print(sum(acertos) / len(acertos))


if __name__ == "__main__":
    testar()
