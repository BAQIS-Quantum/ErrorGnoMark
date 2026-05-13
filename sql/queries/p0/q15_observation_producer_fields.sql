-- p1-step2 API-12 / Q15 Step 1: observation producer fields by id
-- Params: observation_record_id (uuid)
SELECT
    observation_record_id,
    producer_type,
    producer_id,
    source_id
FROM observation_record
WHERE observation_record_id = %(observation_record_id)s::uuid;
