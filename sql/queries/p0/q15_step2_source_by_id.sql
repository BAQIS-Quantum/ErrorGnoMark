-- p1-step2 API-12 / Q15 Step 2: source row for observation.source_id
-- Params: source_id (uuid)
SELECT
    source_id,
    source_name,
    source_type,
    owner_name,
    trust_level
FROM source
WHERE source_id = %(source_id)s::uuid;
