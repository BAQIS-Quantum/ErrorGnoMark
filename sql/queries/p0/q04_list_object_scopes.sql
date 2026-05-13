-- p1-step2 API-04 / Q4 minimal: scopes for a chip
SELECT scope_id, chip_id, scope_type::text AS scope_type, scope_name
FROM scope
WHERE chip_id = %(chip_id)s::uuid
ORDER BY scope_name;
