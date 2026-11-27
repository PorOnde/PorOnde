
from src.rotas import (
    _identificar_pior_trecho,
    calcular_alternativas,
    calcular_rota,
    criar_grafo_simples_para_alternativas,
)


def test_calcular_rotas():
    latitude_origem = -23.583690
    longitude_origem = -46.633915
    latitude_destino = -23.590000
    longitude_destino = -46.640000

    rota = calcular_rota(
        latitude_origem,
        longitude_origem,
        latitude_destino,
        longitude_destino,
    )

    assert rota["distancia_metros"] > 0
    assert rota["tempo_minutos"] > 0
    assert len(rota["nos"]) > 1

    alternativas = calcular_alternativas(
        latitude_origem,
        longitude_origem,
        latitude_destino,
        longitude_destino,
    )

    assert 1 <= len(alternativas) <= 3
    assert alternativas[0]["nome"] == "Mais curta"

    distancia_mais_curta = alternativas[0]["distancia_metros"]
    caminhos = set()

    for alternativa in alternativas:
        # Verifica se o pior trecho foi identificado.
        pior_trecho = alternativa["pior_trecho"]

        fatores = alternativa["fatores"]

        assert fatores["score_iluminacao"] == alternativa["score_iluminacao"]
        assert fatores["score_contexto"] == alternativa["score_contexto"]
        assert (
            fatores["menor_score_contexto"]
            == pior_trecho["score"]
        )

        assert pior_trecho is not None
        assert "origem_no" in pior_trecho
        assert "destino_no" in pior_trecho
        assert 0 <= pior_trecho["score"] <= 100

        # Verifica distância, tempo e nós da rota.
        assert alternativa["distancia_metros"] > 0
        assert alternativa["tempo_minutos"] > 0
        assert len(alternativa["nos"]) > 1

        # Verifica o limite de 40% acima da menor rota.
        assert (
            alternativa["distancia_metros"]
            <= distancia_mais_curta * 1.4
        )

        caminhos.add(tuple(alternativa["nos"]))

    # Verifica se as alternativas possuem caminhos diferentes.
    assert len(caminhos) == len(alternativas)

    print("Teste de rotas concluído.")
    print("Distância:", rota["distancia_metros"], "m")
    print("Tempo:", rota["tempo_minutos"], "min")
    print("Alternativas encontradas:", len(alternativas))

    for alternativa in alternativas:
        print(
            f"- {alternativa['nome']}: "
            f"{alternativa['distancia_metros']} m | "
            f"{alternativa['tempo_minutos']} min"
        )

def test_identificar_pior_trecho():
    import networkx as nx

    grafo = nx.DiGraph()

    grafo.add_edge(1, 2, score_base=80)
    grafo.add_edge(2, 3, score_base=25)
    grafo.add_edge(3, 4, score_base=60)

    pior_trecho = _identificar_pior_trecho(
        grafo,
        [1, 2, 3, 4],
    )

    assert pior_trecho["origem_no"] == 2
    assert pior_trecho["destino_no"] == 3
    assert pior_trecho["score"] == 25

def test_campos_do_grafo_simples():
    import networkx as nx

    grafo = nx.MultiDiGraph()

    grafo.add_edge(
        1,
        2,
        length=100,
        score_iluminacao=75,
        score_base=60,
        n_luz=4,
        n_ocorrencias=2,
        n_abrigos=3,
        em_hotspot=1,
    )

    grafo_simples = criar_grafo_simples_para_alternativas(grafo)

    trecho = grafo_simples[1][2]

    assert trecho["n_luz"] == 4
    assert trecho["n_ocorrencias"] == 2
    assert trecho["n_abrigos"] == 3
    assert trecho["em_hotspot"] == 1
    assert trecho["score_iluminacao"] == 75
    assert trecho["score_base"] == 60
    assert trecho["length"] == 100


if __name__ == "__main__":
    test_calcular_rotas()
