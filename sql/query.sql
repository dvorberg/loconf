BEGIN;

WITH latest AS (
    SELECT cv, address, MAX(revision_id) AS revision_id
      FROM value
      LEFT JOIN revision ON revision_id = revision.id
      GROUP BY cv, address
)
SELECT latest.cv, value, latest.address
  FROM latest
  LEFT JOIN value
         ON latest.cv = value.cv
        AND latest.revision_id = value.revision_id
 WHERE address = 5
 ORDER BY cv
 LIMIT 10;


COMMIT;

