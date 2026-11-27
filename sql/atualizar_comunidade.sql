-- Atualização única, derivada da exportação de funções da equipe.
-- Não recria tabelas nem apaga relatos. Execute como administrador, com backend parado.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
CREATE OR REPLACE FUNCTION public.ativar_alertas()
 RETURNS integer
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
DECLARE
    quantidade INTEGER;
BEGIN
    UPDATE public.relatos AS r
    SET
        status = 'ativo',
        ativado_em = NOW(),
        expira_em = NOW() + CASE
            WHEN r.categoria IN (
                'Iluminação insuficiente',
                'Problema na calçada'
            ) THEN INTERVAL '20 days'

            WHEN r.categoria = 'Obras ou bloqueios'
                THEN INTERVAL '3 days'

            WHEN r.categoria IN (
                'Tumulto ou confusão',
                'Aglomeração comum',
                'Alagamento'
            ) THEN INTERVAL '24 hours'

            ELSE INTERVAL '12 hours'
        END,
        afeta_score = r.categoria IN (
            'Iluminação insuficiente',
            'Obras ou bloqueios',
            'Problema na calçada',
            'Tumulto ou confusão'
        )
    WHERE r.status = 'pendente'
      AND r.categoria <> 'Roubo ou furto relatado'
      AND r.expira_em > NOW()
      AND r.confirmacoes >= r.rejeicoes
      AND public.janela_ativacao_categoria(r.categoria) IS NOT NULL
      AND r.criado_em >= NOW() -
          public.janela_ativacao_categoria(r.categoria)
      AND EXISTS (
          SELECT 1
          FROM public.relatos AS outro
          WHERE outro.id <> r.id
            AND outro.categoria = r.categoria
            AND outro.simulado IS NOT DISTINCT FROM r.simulado
            AND outro.id_sessao <> r.id_sessao
            AND outro.status IN ('pendente', 'ativo')
            AND outro.expira_em > NOW()
            AND outro.confirmacoes >= outro.rejeicoes
            AND outro.criado_em >= NOW() -
                public.janela_ativacao_categoria(r.categoria)
            AND 6371000 * 2 * ASIN(
                SQRT(LEAST(1,
                    POWER(SIN(RADIANS(outro.lat - r.lat) / 2), 2)
                    + COS(RADIANS(r.lat))
                    * COS(RADIANS(outro.lat))
                    * POWER(SIN(RADIANS(outro.lon - r.lon) / 2), 2)
                ))
            ) <= 200
            AND (
                r.categoria <> 'Obras ou bloqueios'
                OR (
                    r.rua IS NOT NULL
                    AND outro.rua IS NOT NULL
                    AND LOWER(TRIM(r.rua)) = LOWER(TRIM(outro.rua))
                )
            )
      );

    GET DIAGNOSTICS quantidade = ROW_COUNT;
    RETURN quantidade;
END;
$function$;

CREATE OR REPLACE FUNCTION public.identificar_recorrencias_roubo_furto()
 RETURNS integer
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
DECLARE
    quantidade INTEGER;
BEGIN
    INSERT INTO public.recorrencias_roubo_furto (
        id_relato_1,
        id_relato_2,
        rua,
        lat,
        lon,
        expira_em
    )
    SELECT
        r1.id,
        r2.id,
        r1.rua,
        (r1.lat + r2.lat) / 2,
        (r1.lon + r2.lon) / 2,
        NOW() + INTERVAL '20 days'
    FROM public.relatos r1
    JOIN public.relatos r2
        ON r1.id < r2.id
       AND r1.categoria = r2.categoria
       AND r1.id_sessao <> r2.id_sessao
       AND r1.simulado IS NOT DISTINCT FROM r2.simulado

    WHERE r1.categoria = 'Roubo ou furto relatado'
      AND r1.status <> 'rejeitado'
      AND r2.status <> 'rejeitado'
      AND r1.confirmacoes >= r1.rejeicoes
      AND r2.confirmacoes >= r2.rejeicoes
      AND r1.rua IS NOT NULL
      AND r2.rua IS NOT NULL
      AND BTRIM(r1.rua) <> ''
      AND BTRIM(r2.rua) <> ''
      AND LOWER(BTRIM(r1.rua)) = LOWER(BTRIM(r2.rua))
      AND r1.ocorrido_em IS NOT NULL
      AND r2.ocorrido_em IS NOT NULL

      -- Validação da primeira ocorrência
      AND (
          CASE
              WHEN r1.horario_informado = TRUE THEN
                  r1.ocorrido_em BETWEEN
                      NOW() - INTERVAL '20 days' AND NOW()
              ELSE
                  (r1.ocorrido_em AT TIME ZONE 'America/Sao_Paulo')::DATE
                  BETWEEN
                      (NOW() AT TIME ZONE 'America/Sao_Paulo')::DATE - 20
                  AND
                      (NOW() AT TIME ZONE 'America/Sao_Paulo')::DATE
          END
      )

      -- Validação da segunda ocorrência
      AND (
          CASE
              WHEN r2.horario_informado = TRUE THEN
                  r2.ocorrido_em BETWEEN
                      NOW() - INTERVAL '20 days' AND NOW()
              ELSE
                  (r2.ocorrido_em AT TIME ZONE 'America/Sao_Paulo')::DATE
                  BETWEEN
                      (NOW() AT TIME ZONE 'America/Sao_Paulo')::DATE - 20
                  AND
                      (NOW() AT TIME ZONE 'America/Sao_Paulo')::DATE
          END
      )

      -- Intervalo entre as ocorrências
      AND (
          CASE
              WHEN r1.horario_informado = TRUE
               AND r2.horario_informado = TRUE THEN
                  ABS(EXTRACT(EPOCH FROM (
                      r1.ocorrido_em - r2.ocorrido_em
                  ))) <= 20 * 24 * 3600
              ELSE
                  ABS(
                      (r1.ocorrido_em AT TIME ZONE 'America/Sao_Paulo')::DATE
                      -
                      (r2.ocorrido_em AT TIME ZONE 'America/Sao_Paulo')::DATE
                  ) <= 20
          END
      )

      -- Regra existente para diferenciar ocorrências
      AND (
          (r1.ocorrido_em AT TIME ZONE 'America/Sao_Paulo')::DATE
          <>
          (r2.ocorrido_em AT TIME ZONE 'America/Sao_Paulo')::DATE
          OR (
              r1.horario_informado = TRUE
              AND r2.horario_informado = TRUE
              AND r1.ocorrido_em <> r2.ocorrido_em
          )
      )

      -- Distância máxima de 200 metros
      AND 6371000 * 2 * ASIN(
          SQRT(LEAST(1,
              POWER(SIN(RADIANS(r2.lat - r1.lat) / 2), 2)
              + COS(RADIANS(r1.lat))
              * COS(RADIANS(r2.lat))
              * POWER(SIN(RADIANS(r2.lon - r1.lon) / 2), 2)
          ))
      ) <= 200

    ON CONFLICT DO NOTHING;

    GET DIAGNOSTICS quantidade = ROW_COUNT;

    RETURN quantidade;
END;
$function$;

CREATE OR REPLACE FUNCTION public.registrar_voto(p_id_relato bigint, p_id_sessao text, p_voto integer)
 RETURNS boolean
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
DECLARE
    v_relato public.relatos%ROWTYPE;
BEGIN
    IF p_voto IS NULL OR p_voto NOT IN (1, -1)
       OR p_id_sessao IS NULL
       OR btrim(p_id_sessao) = '' THEN
        RETURN FALSE;
    END IF;

    SELECT *
    INTO v_relato
    FROM public.relatos
    WHERE id = p_id_relato
    FOR UPDATE;

    IF NOT FOUND
       OR v_relato.id_sessao = p_id_sessao
       OR v_relato.status NOT IN ('pendente', 'ativo')
       OR v_relato.expira_em <= NOW() THEN
        RETURN FALSE;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM public.votos
        WHERE id_relato = p_id_relato
          AND id_sessao = p_id_sessao
    ) THEN
        RETURN FALSE;
    END IF;

    INSERT INTO public.votos (id_relato, id_sessao, voto)
    VALUES (p_id_relato, p_id_sessao, p_voto);

    UPDATE public.relatos
    SET
        confirmacoes = confirmacoes + CASE WHEN p_voto = 1 THEN 1 ELSE 0 END,
        rejeicoes = rejeicoes + CASE WHEN p_voto = -1 THEN 1 ELSE 0 END,

        status = CASE
            WHEN confirmacoes + CASE WHEN p_voto = 1 THEN 1 ELSE 0 END
               - rejeicoes - CASE WHEN p_voto = -1 THEN 1 ELSE 0 END < 0
            THEN 'rejeitado'
            ELSE status
        END,

        afeta_score = CASE
            WHEN confirmacoes + CASE WHEN p_voto = 1 THEN 1 ELSE 0 END
               - rejeicoes - CASE WHEN p_voto = -1 THEN 1 ELSE 0 END < 0
            THEN FALSE
            ELSE afeta_score
        END

    WHERE id = p_id_relato;

    RETURN TRUE;
END;
$function$;

CREATE OR REPLACE FUNCTION public.poronde_isolamento_v1()
RETURNS boolean LANGUAGE sql STABLE SET search_path TO ''
AS $$ SELECT TRUE $$;

-- Apenas backend com credencial de servidor deve acessar os dados comunitários.
-- Frontend não usa acesso direto a essas tabelas. RLS permanece habilitada.
ALTER TABLE public.relatos ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.relatos FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.relatos TO service_role;
ALTER TABLE public.votos ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.votos FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.votos TO service_role;
ALTER TABLE public.verificacoes_alertas ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.verificacoes_alertas FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.verificacoes_alertas TO service_role;
ALTER TABLE public.recorrencias_roubo_furto ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.recorrencias_roubo_furto FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.recorrencias_roubo_furto TO service_role;
REVOKE EXECUTE ON FUNCTION public.ativar_alertas() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.ativar_alertas() TO service_role;
REVOKE EXECUTE ON FUNCTION public.expirar_alertas() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.expirar_alertas() TO service_role;
REVOKE EXECUTE ON FUNCTION public.renovar_alertas() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.renovar_alertas() TO service_role;
REVOKE EXECUTE ON FUNCTION public.registrar_voto(bigint,text,integer) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.registrar_voto(bigint,text,integer) TO service_role;
REVOKE EXECUTE ON FUNCTION public.registrar_verificacao_alerta(bigint,text,boolean) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.registrar_verificacao_alerta(bigint,text,boolean) TO service_role;
REVOKE EXECUTE ON FUNCTION public.identificar_recorrencias_roubo_furto() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.identificar_recorrencias_roubo_furto() TO service_role;
REVOKE EXECUTE ON FUNCTION public.poronde_isolamento_v1() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.poronde_isolamento_v1() TO service_role;

-- Testes transacionais: nenhuma ocorrência temporária permanece no banco.
SAVEPOINT testes_isolamento;
DO $teste$
DECLARE
  real_id bigint;
  demo_id bigint;
  demo2_id bigint;
  prefixo text := 'poronde_isolamento_' || txid_current()::text;
BEGIN
  INSERT INTO public.relatos (categoria,descricao,lat,lon,rua,id_sessao,status,simulado,afeta_score,confirmacoes,rejeicoes,criado_em,expira_em)
  VALUES ('Obras ou bloqueios','Teste temporário',-23.5895,-46.6345,prefixo,prefixo||'_real','pendente',FALSE,FALSE,0,0,NOW(),NOW()+INTERVAL '3 days') RETURNING id INTO real_id;
  INSERT INTO public.relatos (categoria,descricao,lat,lon,rua,id_sessao,status,simulado,afeta_score,confirmacoes,rejeicoes,criado_em,expira_em)
  VALUES ('Obras ou bloqueios','Teste temporário',-23.5896,-46.6345,prefixo,prefixo||'_demo','pendente',TRUE,FALSE,0,0,NOW(),NOW()+INTERVAL '3 days') RETURNING id INTO demo_id;
  PERFORM public.ativar_alertas();
  IF (SELECT count(*) FROM public.relatos WHERE id IN (real_id,demo_id) AND status='pendente') <> 2 THEN
    RAISE EXCEPTION 'Falha: relatos de ambientes diferentes ativaram alerta';
  END IF;
  INSERT INTO public.relatos (categoria,descricao,lat,lon,rua,id_sessao,status,simulado,afeta_score,confirmacoes,rejeicoes,criado_em,expira_em)
  VALUES ('Obras ou bloqueios','Teste temporário',-23.5897,-46.6345,prefixo,prefixo||'_demo2','pendente',TRUE,FALSE,0,0,NOW(),NOW()+INTERVAL '3 days') RETURNING id INTO demo2_id;
  PERFORM public.ativar_alertas();
  IF (SELECT count(*) FROM public.relatos WHERE id IN (demo_id,demo2_id) AND status='ativo' AND afeta_score) <> 2
    OR NOT EXISTS(SELECT 1 FROM public.relatos WHERE id=real_id AND status='pendente') THEN
    RAISE EXCEPTION 'Falha: ativação isolada';
  END IF;
  IF public.registrar_voto(demo_id,prefixo||'_demo',1) IS NOT FALSE THEN
    RAISE EXCEPTION 'Falha: voto próprio permitido';
  END IF;
END;
$teste$;
DO $teste$
DECLARE
    id1 BIGINT;
    id2 BIGINT;
    prefixo TEXT := 'teste_recorrencia_' || txid_current()::text;
BEGIN
    INSERT INTO public.relatos (
        categoria, descricao, lat, lon, rua, id_sessao, status,
        simulado, afeta_score, confirmacoes, rejeicoes,
        criado_em, expira_em, ocorrido_em, horario_informado
    ) VALUES (
        'Roubo ou furto relatado', 'Teste temporário', -23.5895, -46.6345,
        prefixo, prefixo || '_1', 'pendente', TRUE, FALSE, 0, 0,
        NOW(), NOW() + INTERVAL '24 hours', NOW() - INTERVAL '2 days', TRUE
    ) RETURNING id INTO id1;

    PERFORM public.identificar_recorrencias_roubo_furto();
    IF EXISTS (SELECT 1 FROM public.recorrencias_roubo_furto
               WHERE id_relato_1 = id1 OR id_relato_2 = id1) THEN
        RAISE EXCEPTION 'Falha: recorrencia com apenas um relato';
    END IF;

    INSERT INTO public.relatos (
        categoria, descricao, lat, lon, rua, id_sessao, status,
        simulado, afeta_score, confirmacoes, rejeicoes,
        criado_em, expira_em, ocorrido_em, horario_informado
    ) VALUES (
        'Roubo ou furto relatado', 'Teste temporário', -23.5897, -46.6345,
        prefixo, prefixo || '_2', 'pendente', TRUE, FALSE, 0, 0,
        NOW(), NOW() + INTERVAL '24 hours', NOW() - INTERVAL '1 day', TRUE
    ) RETURNING id INTO id2;

    -- Primeiro força os ambientes a diferirem.
    UPDATE public.relatos SET simulado=FALSE WHERE id=id2;
    PERFORM public.identificar_recorrencias_roubo_furto();
    IF EXISTS (SELECT 1 FROM public.recorrencias_roubo_furto WHERE id_relato_1=id1 AND id_relato_2=id2) THEN
        RAISE EXCEPTION 'Falha: recorrência entre ambientes';
    END IF;
    UPDATE public.relatos SET simulado=TRUE WHERE id=id2;
    PERFORM public.identificar_recorrencias_roubo_furto();
    IF NOT EXISTS (SELECT 1 FROM public.recorrencias_roubo_furto
                   WHERE id_relato_1 = id1 AND id_relato_2 = id2
                     AND expira_em > NOW()) THEN
        RAISE EXCEPTION 'Falha: recorrencia nao identificada';
    END IF;
    PERFORM public.identificar_recorrencias_roubo_furto();
    IF (SELECT COUNT(*) FROM public.recorrencias_roubo_furto
        WHERE id_relato_1 = id1 AND id_relato_2 = id2) <> 1 THEN
        RAISE EXCEPTION 'Falha: recorrencia duplicada';
    END IF;
    RAISE NOTICE 'TESTES DE RECORRENCIA APROVADOS';
END;
$teste$;
ROLLBACK TO SAVEPOINT testes_isolamento;
RELEASE SAVEPOINT testes_isolamento;

COMMIT;
SELECT 'Atualização comunitária concluída' AS resultado;
