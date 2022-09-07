CREATE OR REPLACE FUNCTION normalized_entropy(IN tablename VARCHAR, IN attname VARCHAR, OUT entropy NUMERIC)
AS $$
BEGIN
	EXECUTE format('SELECT
	SUM((r1.frequency::NUMERIC / r2.rowcount) * LOG(2, 1 /(r1.frequency::NUMERIC / r2.rowcount))) / COALESCE(NULLIF(LOG(2, COUNT(r1)), 0), 1)
	FROM
		(
		SELECT
			%s,
			COUNT(*) AS frequency
		FROM
			%s
		GROUP BY
			%s ) AS r1,
		(
		SELECT
			COUNT(*) AS rowcount
		FROM
			%s) AS r2;', attname, tablename, attname, tablename)
		INTO entropy;
END $$ LANGUAGE plpgsql;