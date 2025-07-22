-- Verificar todos los constraints CHECK de las tablas
SELECT 
    tc.table_name,
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc 
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'public'
AND tc.table_name IN ('articulos', 'entidades', 'hechos', 'hecho_entidad', 'datos_cuantitativos')
AND tc.constraint_type = 'CHECK'
ORDER BY tc.table_name, tc.constraint_name;