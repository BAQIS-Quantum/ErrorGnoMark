-- p1-step2 API-03 / Q3 minimal: couplers for a chip
SELECT coupler_id, chip_id, coupler_name, coupler_type
FROM coupler
WHERE chip_id = %(chip_id)s::uuid
ORDER BY coupler_name;
