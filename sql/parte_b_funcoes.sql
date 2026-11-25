BEGIN;

-- B12: estrutura da tabela de eventos
CREATE TABLE IF NOT EXISTS public.eventos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (
        tipo IN (
            'busca_trajeto',
            'rota_salva',
            'relato_enviado',
            'voto'
        )
    ),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.eventos ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT ON public.eventos TO service_role;

-- janela_ativacao_categoria
CREATE OR REPLACE FUNCTION public.janela_ativacao_categoria(p_categoria text)
 RETURNS interval
 LANGUAGE sql
 IMMUTABLE
 SET search_path TO ''
AS $function$
    SELECT CASE
        WHEN p_categoria IN (
            'Iluminação insuficiente',
            'Problema na calçada'
        ) THEN INTERVAL '7 days'

        WHEN p_categoria = 'Obras ou bloqueios'
            THEN INTERVAL '24 hours'

        WHEN p_categoria = 'Roubo ou furto relatado'
            THEN INTERVAL '20 days'

        WHEN p_categoria IN (
            'Tumulto ou confusão',
            'Aglomeração comum',
            'Problema no transporte',
            'Alagamento',
            'Outros'
        ) THEN INTERVAL '4 hours'

        ELSE NULL
    END;
$function$;

-- ativar_alertas
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
            'Problema na calçada',nome,codigo
ativar_alertas,"CREATE OR REPLACE FUNCTION public.ativar_alertas()
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
$function$
"
expirar_alertas,"CREATE OR REPLACE FUNCTION public.expirar_alertas()
 RETURNS integer
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
DECLARE
    quantidade INTEGER;
BEGIN
    UPDATE public.relatos
    SET status = 'expirado'
    WHERE status IN ('pendente', 'ativo')
      AND expira_em <= NOW();

    GET DIAGNOSTICS quantidade = ROW_COUNT;

    RETURN quantidade;
END;
$function$
"
identificar_recorrencias_roubo_furto,"CREATE OR REPLACE FUNCTION public.identificar_recorrencias_roubo_furto()
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
      AND r1.ocorrido_em BETWEEN NOW() - INTERVAL '20 days' AND NOW()
      AND r2.ocorrido_em BETWEEN NOW() - INTERVAL '20 days' AND NOW()
      AND ABS(EXTRACT(EPOCH FROM (
          r1.ocorrido_em - r2.ocorrido_em
      ))) <= 20 * 24 * 3600
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
$function$
"
janela_ativacao_categoria,"CREATE OR REPLACE FUNCTION public.janela_ativacao_categoria(p_categoria text)
 RETURNS interval
 LANGUAGE sql
 IMMUTABLE
 SET search_path TO ''
AS $function$
    SELECT CASE
        WHEN p_categoria IN (
            'Iluminação insuficiente',
            'Problema na calçada'
        ) THEN INTERVAL '7 days'

        WHEN p_categoria = 'Obras ou bloqueios'
            THEN INTERVAL '24 hours'

        WHEN p_categoria = 'Roubo ou furto relatado'
            THEN INTERVAL '20 days'

        WHEN p_categoria IN (
            'Tumulto ou confusão',
            'Aglomeração comum',
            'Problema no transporte',
            'Alagamento',
            'Outros'
        ) THEN INTERVAL '4 hours'

        ELSE NULL
    END;
$function$
"
registrar_verificacao_alerta,"CREATE OR REPLACE FUNCTION public.registrar_verificacao_alerta(p_id_relato bigint, p_id_sessao text, p_continua boolean)
 RETURNS boolean
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
DECLARE
    v_relato public.relatos%ROWTYPE;
    v_negativas INTEGER;
    v_positivas INTEGER;
BEGIN
    IF p_id_relato IS NULL
       OR p_id_sessao IS NULL
       OR BTRIM(p_id_sessao) = ''
       OR p_continua IS NULL THEN
        RETURN FALSE;
    END IF;

    SELECT *
    INTO v_relato
    FROM public.relatos
    WHERE id = p_id_relato
    FOR UPDATE;

    IF NOT FOUND
       OR v_relato.status <> 'ativo'
       OR v_relato.expira_em <= NOW() THEN
        RETURN FALSE;
    END IF;

    -- Impede respostas repetidas da mesma sessão em 2 horas.
    IF EXISTS (
        SELECT 1
        FROM public.verificacoes_alertas
        WHERE id_relato = p_id_relato
          AND id_sessao = p_id_sessao
          AND criado_em > NOW() - INTERVAL '2 hours'
    ) THEN
        RETURN FALSE;
    END IF;

    INSERT INTO public.verificacoes_alertas (
        id_relato, id_sessao, continua
    )
    VALUES (p_id_relato, p_id_sessao, p_continua);

    -- Encerramento antecipado apenas para tumulto.
    IF v_relato.categoria = 'Tumulto ou confusão' THEN

        SELECT
            COUNT(DISTINCT id_sessao)
                FILTER (WHERE continua = FALSE),
            COUNT(DISTINCT id_sessao)
                FILTER (WHERE continua = TRUE)
        INTO v_negativas, v_positivas
        FROM public.verificacoes_alertas
        WHERE id_relato = p_id_relato
          AND criado_em > NOW() - INTERVAL '2 hours';

        IF v_negativas >= 3 AND v_positivas = 0 THEN
            UPDATE public.relatos
            SET status = 'expirado',
                expira_em = NOW(),
                afeta_score = FALSE
            WHERE id = p_id_relato;
        END IF;
    END IF;

    RETURN TRUE;
END;
$function$
"
registrar_voto,"CREATE OR REPLACE FUNCTION public.registrar_voto(p_id_relato bigint, p_id_sessao text, p_voto integer)
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
        END
    WHERE id = p_id_relato;

    RETURN TRUE;
END;
$function$
"
renovar_alertas,"CREATE OR REPLACE FUNCTION public.renovar_alertas()
 RETURNS integer
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
DECLARE
    quantidade INTEGER;
BEGIN
    UPDATE public.relatos AS r
    SET
        renovado_em = NOW(),
        expira_em = NOW() + CASE
            WHEN r.categoria IN (
                'Iluminação insuficiente',
                'Problema na calçada'
            ) THEN INTERVAL '20 days'
            ELSE INTERVAL '3 days'
        END
    WHERE r.status = 'ativo'
      AND r.categoria IN (
          'Iluminação insuficiente',
          'Problema na calçada',
          'Obras ou bloqueios'
      )
      AND r.expira_em > NOW()
      AND r.expira_em <= NOW() + INTERVAL '48 hours'
      AND (
          SELECT COUNT(DISTINCT v.id_sessao)
          FROM public.verificacoes_alertas AS v
          WHERE v.id_relato = r.id
            AND v.continua = TRUE
            AND v.criado_em > NOW() - INTERVAL '48 hours'
            AND (
                r.renovado_em IS NULL
                OR v.criado_em > r.renovado_em
            )
      ) >= 2;

    GET DIAGNOSTICS quantidade = ROW_COUNT;
    RETURN quantidade;
END;
$function$
"