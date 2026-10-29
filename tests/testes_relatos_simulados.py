import os

os.environ["PORONDE_MODO"] = "demo"

from src import relatos


BBOX_DE_TESTE = (-23.60, -23.50, -46.70, -46.60)

relatos._obter_bbox_vm = lambda: BBOX_DE_TESTE

try:
    quantidade = relatos.gerar_relatos_simulados()
    alertas = relatos.listar_alertas_ativos()

    assert quantidade == 15
    assert len(alertas) >= 6
    assert list(alertas.columns) == relatos.COLUNAS_ALERTAS

    print(f"Relatos criados: {quantidade}")
    print(f"Alertas ativos: {len(alertas)}")
    print("Teste dos relatos simulados concluído.")
finally:
    relatos.limpar_simulados()