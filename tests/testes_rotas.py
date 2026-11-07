from src.rotas import calcular_alternativas, calcular_rota


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
        assert alternativa["distancia_metros"] > 0
        assert alternativa["tempo_minutos"] > 0
        assert len(alternativa["nos"]) > 1

        assert (
            alternativa["distancia_metros"]
            <= distancia_mais_curta * 1.4
        )

        caminhos.add(tuple(alternativa["nos"]))

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


if __name__ == "__main__":
    test_calcular_rotas()