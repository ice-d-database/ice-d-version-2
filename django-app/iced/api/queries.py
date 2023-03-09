def leafletmap_query(application_name):
    return f"""
with data as (
select samples.name as sample_name,
                     samples.lat_DD as lat,
                     samples.lon_DD as lon,
                     samples.what as what,
                     sites.short_name as site_shortname,
                     sites.name as site_longname,
                     sites.id as site_id,
                     `range` as `range`,
                     siteregions.name as region
                     from base_sample samples
                     left join base_site sites on sites.id = samples.site_id
                     left join base_region siteregions on siteregions.id = sites.region_id
                     left join base_application_sites cas on cas.site_id = sites.id
                     left join base_application application on application.id = cas.application_id
where application.name = '{application_name}'
), hash_records as (
select ST_GeoHash(lon, lat, 2) as geohash,
    lon,
    lat,
    sample_name
    from data
), region_data as (
    select
    JSON_OBJECT(
        'type', 'Feature',
        'geometry', JSON_OBJECT('type', 'Point', 'coordinates', JSON_ARRAY(round(avg(lon), 5), round(avg(lat) ,5))), -- gives it a less uniform grid feel than using the geohash functions to generate
        'properties', JSON_OBJECT('region', geohash, 'nsamples', count(sample_name))
    ) as obj
    from hash_records
    group by geohash
), sample_data as (
    select JSON_OBJECT(
        "type", "Feature",
        'geometry', JSON_OBJECT('type', 'Point', 'coordinates', json_array(round(lon, 5), round(lat, 5))),
        'properties', JSON_OBJECT(
                'sample_name', sample_name,
                'what', what,
                'site', site_shortname,
                'site_longname', site_longname,
                'site_id', site_id,
                'region', region
            )
        ) as obj
    from data
), region_json as (
    select JSON_OBJECT(
    "type", "FeatureCollection",
    "name", "ICED_regions",
    "crs", JSON_OBJECT("type", "name", "properties", JSON_OBJECT("name", "urn:ogc:def:crs:OGC:1.3:CRS84")),
    "features", JSON_ARRAYAGG(region_data.obj)
    ) as data
            from region_data
), sample_json as (
    select JSON_OBJECT(
    "type", "FeatureCollection",
    "name", "ICED_samples",
    "crs", JSON_OBJECT("type", "name", "properties", JSON_OBJECT("name", "urn:ogc:def:crs:OGC:1.3:CRS84")),
    "features", JSON_ARRAYAGG(sample_data.obj)
    ) as data
    from sample_data
)select JSON_OBJECT("regions", region_json.data, "samples", sample_json.data) from region_json, sample_json
"""
