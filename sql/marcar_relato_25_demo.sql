-- OPCIONAL: execute somente se confirmar que o relato 25 e seu voto são de demonstração.
-- Mantém o registro e os votos, mas não os exibe na comunidade real.
BEGIN;
UPDATE public.relatos SET simulado = TRUE
WHERE id = 25 AND categoria = 'Problema na calçada' AND descricao = 'Problema na calçada'
  AND status = 'pendente' AND simulado = FALSE;
COMMIT;
SELECT id, categoria, status, simulado FROM public.relatos WHERE id=25;
