-- p1-step2 API-01 / Q1 minimal: chip row by id
-- Param: chip_id (uuid)
SELECT chip_id, chip_name, generation_name, vendor, status, created_at
FROM chip
WHERE chip_id = %(chip_id)s::uuid;
