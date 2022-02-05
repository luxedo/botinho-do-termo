import random
import termo

TAMANHO = 5
RODADAS = 200
# termo.PALAVRAS_INICIAIS = 1


def simular_jogo(palavra):
    tentativas = []
    resultados = []
    tentativa = termo.resolver([], [])
    for i in range(1, 7):
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
        tentativa = termo.resolver(tentativas, resultados)
        # if tentativa is None:
        #     return 6
    return 7


def testar():
    wordlist = termo.carregar_wordlist(TAMANHO, False)
    tf = termo.carregar_tf(TAMANHO, False)
    acertos = []
    for i in range(RODADAS):
        palavra = random.choice(wordlist)[0]
        acertos.append(simular_jogo(palavra))
    print(acertos)
    print(sum(acertos) / len(acertos))


if __name__ == "__main__":
    testar()
