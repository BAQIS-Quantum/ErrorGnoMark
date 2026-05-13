-- q25: Full-chip calibration heatmap data for a specific calibration run.
-- Returns per-qubit metrics for rendering a T1/T2/fidelity heatmap.
-- Parameters: :calibration_run_id
--
-- Example:
--   cur.execute(open('q25_...sql').read(),
--               {"calibration_run_id": "<uuid>"})

SELECT
    q.qubit_index,
    md.metric_name,
    o.value_numeric,
    o.quality_flag
FROM observation_record o
JOIN calibration_artifact ca
    ON  ca.calibration_artifact_id = o.producer_id
    AND o.producer_type = 'calibration_artifact'
JOIN metric_definition md
    ON md.metric_definition_id = o.metric_definition_id
JOIN qubit q
    ON  q.qubit_id = o.subject_id
    AND o.subject_type = 'qubit'
WHERE ca.calibration_run_id = :calibration_run_id ::uuid
    AND md.metric_family = 'quafu_calibration'
ORDER BY q.qubit_index, md.metric_name;
