WITH samples AS (SELECT base_sample.id,
                        coord,
                        lon_DD                                                                       AS lon,
                        lat_DD                                                                       AS lat,
                        elv_m,
                        base_sample.name,
                        site.short_name                                                              AS site_name,
                        site.site_truet,
                        site.site_del_truet,
                        base_sample.what,
                        lithology,
                        collected_by,
                        date_collected,
                        CONCAT('https://version2.ice-d.org/%application%/sample/', base_sample.name) AS sample_url,
                        CONCAT('https://version2.ice-d.org/%application%/site/', site.short_name)    AS site_url
                 FROM base_sample
                          INNER JOIN base_site AS site ON base_sample.site_id = site.id
                          INNER JOIN base_application_sites AS app_mapping ON site.id = app_mapping.site_id
                          INNER JOIN base_application AS app ON app_mapping.application_id = app.id
                 WHERE LOWER(app.name) = '%application%')
SELECT samples.id,
       samples.coord,
       samples.lon,
       samples.lat,
       samples.elv_m,
       samples.name,
       samples.site_name,
       samples.site_truet,
       samples.site_del_truet,
       samples.what,
       samples.lithology,
       samples.collected_by,
       samples.date_collected,
       samples.sample_url,
       samples.site_url,
       (SELECT CONCAT(
                       '[\'',
                       GROUP_CONCAT(DISTINCT COALESCE(
                               pub.doi,
                               CONCAT('Unknown DOI - ', pub.short_name)
                           ) SEPARATOR '\', \''),
                       '\']'
                   )
        FROM samples AS s
                 LEFT JOIN base_samplepublicationsmatch AS pub_mapping ON s.id = pub_mapping.sample_id
                 LEFT JOIN base_publication AS pub ON pub_mapping.publication_id = pub.id
        WHERE s.id = samples.id
        GROUP BY samples.id) AS publications,
       age.id                AS age_id,
       age.nuclide,
       age.t_St,
       age.dtint_St,
       age.t_LSDn,
       age.dtint_LSDn
FROM samples
         LEFT JOIN base_calculatedage AS age ON samples.id = age.sample_id
