SELECT (dp).path, ST_AsText((dp).geom) AS geog_point
FROM (SELECT ST_DumpPoints(ST_Transform(ST_Segmentize(geom_path, 50), 4326)) AS dp
     FROM trips
     WHERE trip_id = 1) as foo;
     
