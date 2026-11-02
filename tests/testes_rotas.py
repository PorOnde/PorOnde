from src.rotas import calcular_rota


def executar_teste():
    rota = calcular_rota(
        -23.583690,
        -46.633915,
        -23.590000,
        -46.640000,
    )

    assert rota["distancia_metros"] > 0
    assert rota["tempo_minutos"] > 0
    assert len(rota["nos"]) > 1

    print("Teste de rotas concluído.")
    print("Distância:", rota["distancia_metros"], "m")
    print("Tempo:", rota["tempo_minutos"], "min")


if __name__ == "__main__":
    executar_teste()