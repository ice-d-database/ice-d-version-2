SELECT core.id,
       coord,
       lon_DD                                                                    AS lon,
       lat_DD                                                                    AS lat,
       elv_m,
       core.name,
       site.short_name                                                           AS site_name,
       core.what,
       collected_by,
       date_collected,
       core.comments,
       CONCAT('https://version2.ice-d.org/%application%/core/', core.name)       AS core_url,
       CONCAT('https://version2.ice-d.org/%application%/site/', site.short_name) AS site_url,
       CONCAT('[\'',
              GROUP_CONCAT(DISTINCT COALESCE(pub.doi, CONCAT('Unknown DOI - ', pub.short_name)) SEPARATOR '\', \''),
              '\']')                                                             AS publications
FROM base_core AS core
         INNER JOIN base_site AS site ON core.site_id = site.id
         INNER JOIN base_application_sites AS app_mapping ON site.id = app_mapping.site_id
         INNER JOIN base_application AS app ON app_mapping.application_id = app.id
         LEFT JOIN base_coresample AS core_sample ON core.id = core_sample.core_id
         LEFT JOIN base_samplepublicationsmatch AS pub_mapping ON core_sample.id = pub_mapping.core_sample_id
         LEFT JOIN base_publication AS pub ON pub_mapping.publication_id = pub.id
WHERE LOWER(app.name) = '%application%'
GROUP BY core.id