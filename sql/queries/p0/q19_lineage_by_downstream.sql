-- p1-step2 API-14 / Q19–Q21 Step 1: lineage header for downstream object
-- Params: downstream_object_type (text → lineage_object_type_enum), downstream_object_id (uuid)
SELECT
    lineage_id,
    downstream_object_type,
    downstream_object_id,
    transformation_type,
    method_version_id,
    computed_at,
    created_at
FROM lineage
WHERE downstream_object_type = %(downstream_object_type)s::lineage_object_type_enum
  AND downstream_object_id = %(downstream_object_id)s::uuid;
