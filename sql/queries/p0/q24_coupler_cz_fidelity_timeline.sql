-- q24: CZ fidelity timeline for a specific coupler across calibration runs.
-- Parameters: :coupler_id, :limit_n
--
-- Example (psycopg):
--   cur.execute(open('q24_...sql').read(),
--               {"coupler_id": "<uuid>", "limit_n": 20})

SELECT
    o.observation_time,
    o.value_numeric    AS cz_fidelity,
    o.quality_flag,
    cr.start_time      AS calibration_time,
    cr.calibration_run_id
FROM observation_record o
JOIN calibration_artifact ca
    ON  ca.calibration_artifact_id = o.producer_id
    AND o.producer_type = 'calibration_artifact'
JOIN calibration_run cr
    ON cr.calibration_run_id = ca.calibration_run_id
WHERE o.subject_type = 'coupler'
    AND o.subject_id = :coupler_id ::uuid
    AND o.metric_definition_id = (
        SELECT metric_definition_id FROM metric_definition
        WHERE metric_name = 'quafu_cz_fidelity'
    )
ORDER BY o.observation_time DESC
LIMIT :limit_n;
