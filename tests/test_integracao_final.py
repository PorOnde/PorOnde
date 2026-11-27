"""Testes locais. Não consultam nem gravam no Supabase e não geocodificam pela internet."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from fastapi.testclient import TestClient
import api
from src import config, score, rotas
from src.catalogo_enderecos import sugerir, normalizar


class TesteProjeto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Coordenadas do piloto; não representam relatos de ocorrências.
        cls.coordenadas = (-23.58945, -46.63405, -23.592, -46.638)
        cls.rotas = rotas.calcular_alternativas(*cls.coordenadas, alertas_ativos=pd.DataFrame())
        cls.curta = cls.rotas[0]
        arquivo = score.TRATADOS / 'grafo_vila_mariana.graphml'
        linhas = score._linhas_projetadas(arquivo, arquivo.stat().st_mtime_ns)
        cls.linha = linhas.loc[cls.curta['edge_ids']].union_all()
        ponto = cls.linha.centroid
        ponto = cls.linha.interpolate(cls.linha.project(ponto))
        import geopandas as gpd
        ponto = gpd.GeoSeries([ponto], crs=linhas.crs).to_crs('EPSG:4326').iloc[0]
        cls.lat, cls.lon = float(ponto.y), float(ponto.x)

    def test_catalogo_local(self):
        resultado = sugerir('gandava')
        self.assertTrue(any('gandavo' in normalizar(r) for r in resultado), resultado)
        self.assertEqual(sugerir('Rua Gandava 99999'), [])

    def test_rotas_reais(self):
        self.assertTrue(1 <= len(self.rotas) <= 3)
        self.assertEqual(self.curta['nome'], 'Mais curta')
        for rota in self.rotas:
            self.assertLessEqual(rota['distancia_metros'], self.curta['distancia_metros'] * 1.4 + 2)
            self.assertTrue(0 <= rota['score_contexto'] <= 100)
            self.assertTrue(rota['edge_ids'])

    def _relato(self, id, status='ativo', afeta=True, distante=False):
        return {'id': id, 'lat': self.lat + (0.02 if distante else 0), 'lon': self.lon,
                'status': status, 'afeta_score': afeta, 'categoria': 'Problema na calçada'}

    def test_filtro_e_penalidade(self):
        registros = [self._relato(1), self._relato(2, 'pendente', False),
                     self._relato(3, 'ativo', False), self._relato(4, distante=True)]
        proximos = api._relatos_proximos(self.curta['edge_ids'], registros)
        self.assertEqual({r['id'] for r in proximos}, {1,2,3})
        elegiveis = api._relatos_para_score(registros)
        self.assertEqual(set(elegiveis['id']), {1,4})
        base = score.avaliar_rota(self.curta['edge_ids'], pd.DataFrame())
        nova = score.avaliar_rota(self.curta['edge_ids'], elegiveis)
        self.assertEqual(nova['n_alertas_na_rota'], 1)
        self.assertEqual(nova['penalidade_alertas'], 10)
        self.assertAlmostEqual(nova['score_medio'], max(0, base['score_medio'] - 10))
        muitos = pd.DataFrame([self._relato(i) for i in range(10,14)])
        self.assertEqual(score.avaliar_rota(self.curta['edge_ids'], muitos)['penalidade_alertas'], 30)

    def test_api_rotas_com_alerta_e_falha(self):
        registros = [self._relato(1), self._relato(2, 'pendente', False)]
        with patch.object(api, '_consultar_relatos_validos', return_value=registros), patch.object(api, '_recorrencias_ou_indisponivel', return_value=[]):
            r = api.buscar_rotas(*self.coordenadas)
            self.assertTrue(r['alertas_disponiveis'])
            self.assertEqual(r['rotas'][0]['avaliacao']['penalidade_alertas'], 10)
            self.assertEqual({x['id'] for x in r['rotas'][0]['relatos_proximos']}, {1,2})
        with patch.object(api, '_consultar_relatos_validos', side_effect=RuntimeError('falha simulada')):
            r = api.buscar_rotas(*self.coordenadas)
            self.assertFalse(r['alertas_disponiveis'])
            self.assertIsNone(r['rotas'][0]['relatos_proximos'])

    def test_recorrencias(self):
        from src import supabase_db
        fontes=[{'id':1,'status':'pendente','simulado':api.SIMULADO},
                {'id':2,'status':'pendente','simulado':api.SIMULADO},
                {'id':3,'status':'pendente','simulado':not api.SIMULADO},
                {'id':4,'status':'rejeitado','simulado':api.SIMULADO}]
        class Consulta:
            def select(self,*a): return self
            def in_(self,*a): return self
            def execute(self): return SimpleNamespace(data=fontes)
        registros=[dict(id_relato_1=1,id_relato_2=i,rua='Rua de teste',lat=self.lat,lon=self.lon,expira_em='2099-01-01') for i in (2,3,4)]
        with patch.object(supabase_db,'listar_recorrencias_ativas_supabase',return_value=registros), patch.object(supabase_db,'conectar_supabase',return_value=SimpleNamespace(table=lambda _:Consulta())):
            self.assertEqual([r['id'] for r in api._consultar_recorrencias()],['1-2'])

    def test_http(self):
        c = TestClient(api.app)
        self.assertEqual(c.get('/api/saude').json(), {'status':'online'})
        self.assertIn('simulado', c.get('/api/ambiente').json())
        self.assertEqual(c.get('/api/enderecos/sugestoes', params={'q':'Gandava'}).status_code, 200)
        self.assertEqual(c.get('/api/rotas', params={'origem_lat':0,'origem_lon':0,'destino_lat':1,'destino_lon':1}).status_code, 400)
        # Nenhum endpoint mutante usa banco real durante o teste.
        with patch.object(api, '_confirmar_isolamento_sql', return_value=True), patch('src.supabase_db.registrar_relato_supabase', return_value=123) as registrar:
            dados = {'categoria':'Problema na calçada','descricao':'teste local','lat':self.lat,'lon':self.lon,'id_sessao':'sessao_teste'}
            r = c.post('/api/relatos', json=dados)
            self.assertEqual(r.status_code,201)
            self.assertEqual(registrar.call_args.kwargs['simulado'], api.SIMULADO)
            self.assertEqual(r.json()['simulado'],api.SIMULADO)
            dados['categoria']='Roubo ou furto relatado'
            self.assertEqual(c.post('/api/relatos',json=dados).status_code,400)

    def test_voto_continuidade_isolados(self):
        c=TestClient(api.app)
        class Consulta:
            def __init__(self): self.id = None
            def select(self,*a): return self
            def eq(self,k,v): self.id=v; return self
            def limit(self,*a): return self
            def execute(self):
                item={'id_sessao':'autor','status':'ativo','categoria':'Problema na calçada','simulado': api.SIMULADO if self.id==1 else not api.SIMULADO}
                return SimpleNamespace(data=[item])
        conexao=SimpleNamespace(table=lambda _: Consulta())
        with patch.object(api,'_confirmar_isolamento_sql',return_value=True), patch('src.supabase_db.conectar_supabase',return_value=conexao), patch('src.supabase_db.votar_supabase',return_value=True) as voto, patch('src.supabase_db.registrar_verificacao_supabase',return_value=True) as verificar:
            url='/api/comunidade/relatos/{}/voto'
            self.assertEqual(c.post(url.format(1),json={'id_sessao':'autor','voto':1}).status_code,409)
            self.assertEqual(c.post(url.format(2),json={'id_sessao':'outro','voto':1}).status_code,404)
            self.assertEqual(c.post(url.format(1),json={'id_sessao':'outro','voto':1}).status_code,200)
            self.assertEqual(voto.call_count,1)
            self.assertEqual(c.post('/api/comunidade/relatos/2/verificacao',json={'id_sessao':'outro','continua':True}).status_code,404)
            self.assertEqual(c.post('/api/comunidade/relatos/1/verificacao',json={'id_sessao':'outro','continua':True}).status_code,200)
            self.assertEqual(verificar.call_count,1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
