def exposure_calculator_string_query(sample_ids: str, known_age: bool = False) -> str:
    known_age_query = """
calibration_text as (
    select s.id,
           s.name,
           concat_ws(" ",
                 s.name,
                 "true_t",
                 st.short_name,
                 case
                      when st.site_truet is not null
                          then concat_ws(" ",
                                         st.site_truet, st.site_del_truet
                          )
                      else concat_ws(" ",
                          coalesce(st.site_max_truet, 0),
                         coalesce(st.site_del_max_truet, 0),
                         coalesce(st.site_min_truet, 0),
                         coalesce(st.site_del_min_truet, 0)
                      )
                end,
                ";"
           ) as c_text
    from sample s
    left join base_site st on st.id = s.site_id
),
"""

    sql =  f"""
with sample as (
    select *
    from base_sample
    where id in ({','.join([str(sample_id) for sample_id in sample_ids])})
),
 sample_text as (
     select id,
            name,
            concat_ws(" ",
                  name,
                  case -- We check if both lat/lon is entered (we need both to be useful)
                      when lat_dd is not null and lon_DD is not null
                          then concat_ws(" ",
                                         truncate(lat_DD, 5),
                                         truncate(lon_DD, 5)
                          )
                      else ""
                      end,
                  coalesce(truncate(elv_m, 5), ""),
                  case
                      when lat_DD < -60 then "ant" -- lat below -60 = antarctica
                      else "std"
                      end,
                  coalesce(truncate(thick_cm, 1), 1),
                  coalesce(truncate(density, 2), 1),
                  coalesce(truncate(shielding, 4), 1),
                  "0", -- why?
                  coalesce(year(date_collected), 0),
                  ";"
            ) as sample_text
     from sample
 ),
 {known_age_query if known_age else ""}
 be10_text as (
     select s.id,
            group_concat(
                    concat_ws(" ",
                          case
                              when be10.N10_atoms_g is not null
                                  and be10.delN10_atoms_g is not null
                                  and be10.Be10_std is not null
                                  and be10.N10_atoms_g > 0
                                  and be10.delN10_atoms_g > 0
                                  then concat_ws(" ",
                                                 concat(name, " ", "Be-10 quartz"),
                                                 truncate(be10.N10_atoms_g, 3),
                                                 truncate(be10.delN10_atoms_g, 3),
                                                 be10.Be10_std,
                                                 ";\n"
                                  )
                              end,
                          case
                              when be10.N26_atoms_g is not null
                                  and be10.delN26_atoms_g is not null
                                  and be10.Al26_std is not null
                                  and be10.N26_atoms_g > 0
                                  and be10.delN26_atoms_g > 0
                                  then concat_ws(" ",
                                                 concat(name, " ", "Al-26 quartz"),
                                                 truncate(be10.N26_atoms_g, 3),
                                                 truncate(be10.delN26_atoms_g, 3),
                                                 be10.Al26_std,
                                                 ";\n"
                                  )
                              end
                    )
                    SEPARATOR ' ') as be10_text
     from sample s
              left join _be10_al26_quartz be10 on s.id = be10.sample_id
     group by s.id
 ),
 he3quartz_text as (
     select s.id,
            group_concat(
                    concat_ws(" ",
                          case
                              when he3quartz.N3c_atoms_g is not null
                                  and he3quartz.delN3c_atoms_g is not null
                                  and he3quartz.N3c_atoms_g > 0
                                  and he3quartz.delN3c_atoms_g > 0
                                  then concat_ws(" ",
                                                 concat(name, " ", "He-3 quartz"),
                                                 truncate(he3quartz.N3c_atoms_g, 3),
                                                 truncate(he3quartz.delN3c_atoms_g, 3),
                                                 case
                                                     when he3quartz.standard is not null
                                                         and he3quartz.std_N3_atoms_g is not null
                                                         then concat_ws(" ",
                                                                        concat(he3quartz.standard),
                                                                        truncate(he3quartz.std_N3_atoms_g, 3),
                                                                        ";\n"
                                                         )
                                                     else "NONE 0;\n"
                                                     end
                                  )
                              end
                    )
                    SEPARATOR ' ') as he3quartz_text
     from sample s
              left join _he3_quartz he3quartz on s.id = he3quartz.sample_id
     group by s.id
 ),
 he3pxol_text as (
     select s.id,
            group_concat(
                    concat_ws(" ",
                          case
                              when he3pxol.N3c_atoms_g is not null
                                  and he3pxol.delN3c_atoms_g is not null
                                  and he3pxol.N3c_atoms_g > 0
                                  and he3pxol.delN3c_atoms_g > 0
                                  then concat_ws(" ",
                                                 concat(name, " ", "He-3"),
                                                 (case
                                                      when he3pxol.mineral in
                                                           ('Cpx', 'Pyroxene', 'cpx', 'opx', 'px', 'pyroxene',
                                                            'clinopyroxene', 'orthopyroxene', 'augite',
                                                            'enstatite', 'diopside', 'Green diopside')
                                                          then "pyroxene"
                                                      else "olivine"
                                                     end),
                                                 truncate(he3pxol.N3c_atoms_g, 3),
                                                 truncate(he3pxol.delN3c_atoms_g, 3),
                                                 case
                                                     when he3pxol.standard is not null
                                                         and he3pxol.std_N3_atoms_g is not null
                                                         then concat_ws(" ",
                                                                        concat(he3pxol.standard),
                                                                        truncate(he3pxol.std_N3_atoms_g, 3),
                                                                        ";\n"
                                                         )
                                                     else "NONE 0;\n"
                                                     end
                                  )
                              end
                    )
                    SEPARATOR ' ') as he3pxol_text
     from sample s
              left join _he3_pxol he3pxol on s.id = he3pxol.sample_id
     group by s.id
 ),
 ne21quartz_text as (
     select s.id,
            group_concat(
                    concat_ws(" ",
                          case
                              when ne21quartz.N21xs_atoms_g is not null
                                  and ne21quartz.delN21xs_atoms_g is not null
                                  and ne21quartz.N21xs_atoms_g > 0
                                  and ne21quartz.delN21xs_atoms_g > 0
                                  then concat_ws(" ",
                                                 concat(name, " ", "Ne-21 quartz"),
                                                 truncate(ne21quartz.N21xs_atoms_g, 3),
                                                 truncate(ne21quartz.delN21xs_atoms_g, 3),
                                                 case
                                                     when ne21quartz.standard is not null
                                                         and ne21quartz.std_N21c_atoms_g is not null
                                                         then concat_ws(" ",
                                                                        concat(ne21quartz.standard),
                                                                        truncate(ne21quartz.std_N21c_atoms_g, 3),
                                                                        ";\n"
                                                         )
                                                     else "NONE 0;\n"
                                                     end
                                  )
                              end
                    )
                    SEPARATOR ' ') as ne21quartz_text
     from sample s
              left join _ne21_quartz ne21quartz on s.id = ne21quartz.sample_id
     group by s.id
 ),
 c14quartz_text as (
     select s.id,
            group_concat(
                    concat_ws(" ",
                          case
                              when c14quartz.N14_atoms_g is not null
                                  and c14quartz.delN14_atoms_g is not null
                                  and c14quartz.N14_atoms_g > 0
                                  and c14quartz.delN14_atoms_g > 0
                                  then concat_ws(" ",
                                                 concat(name, " ", "C-14 quartz"),
                                                 truncate(c14quartz.N14_atoms_g, 3),
                                                 truncate(c14quartz.delN14_atoms_g, 3),
                                                 ";\n"
                                  )
                              end
                    )
                    SEPARATOR ' ') as c14quartz_text
     from sample s
              left join _c14_quartz c14quartz on s.id = c14quartz.sample_id
     group by s.id
 )
select st.id,
       st.name,
       case when {"ct.c_text REGEXP ';' and ( " if known_age else ""}b10.be10_text REGEXP ';' or he3q.he3quartz_text REGEXP ';' or he3p.he3pxol_text REGEXP ';' or
                 ne21.ne21quartz_text REGEXP ';' or c14.c14quartz_text REGEXP ';' {")" if known_age else ""}
       then
            concat_ws("\n", st.sample_text,{"ct.c_text, " if known_age else " "}b10.be10_text, he3q.he3quartz_text, he3p.he3pxol_text, ne21.ne21quartz_text,
                 c14.c14quartz_text)
       else ""
       end as output
from sample_text st
         {"left join calibration_text ct on st.id = ct.id" if known_age else ""}
         left join be10_text b10 on st.id = b10.id
         left join he3quartz_text he3q on st.id = he3q.id
         left join he3pxol_text he3p on st.id = he3p.id
         left join ne21quartz_text ne21 on st.id = ne21.id
         left join c14quartz_text c14 on st.id = c14.id
"""

    return sql


def cl36_calculator_string_query(sample_ids: str) -> str:
    return f"""
with sample as (
    select *
    from base_sample
    where id in ({','.join([str(sample_id) for sample_id in sample_ids])})
),
 sample_text as (
     select id,
            name,
            concat_ws(" ",
                      name,
                      case -- We check if both lat/lon is entered (we need both to be useful)
                          when lat_dd is not null and lon_DD is not null
                              then concat_ws(" ",
                                             truncate(lat_DD, 5),
                                             truncate(lon_DD, 5)
                              )
                          else ""
                          end,
                      coalesce(truncate(elv_m, 5), ""),
                      case
                          when lat_DD < -60 then "ant" -- lat below -60 = antarctica
                          else "std"
                          end,
                      coalesce(truncate(thick_cm, 1), 1),
                      coalesce(truncate(density, 2), 1),
                      coalesce(truncate(shielding, 4), 1),
                      "0", -- why?
                      coalesce(year(date_collected), 0),
                      ";"
                ) as sample_text
     from sample
 ), cl36_text as (
         select s.id,
                group_concat(
                        concat_ws(" ",
                                  case
                                      when
                                          cl36.N36_atoms_g > 0 and cl36.delN36_atoms_g > 0
                                          then concat_ws(" ",
                                                         name,
                                                         coalesce(aliquot,""),
                                                         "Cl-36",
                                                         truncate(N36_atoms_g, 3),
                                                         truncate(delN36_atoms_g, 3),
                                                         truncate(target_Cl_ppm, 2),
                                                         truncate(deltarget_Cl_ppm, 2),
                                                         ";"
                                          )
                                      else "" end
                        )
                SEPARATOR ' ') as cl36_text
         from sample s
                  left join _cl36 cl36 on s.id = cl36.sample_id
         group by s.id
     ), formation_age_text as (
         select s.id,
                group_concat(
                        concat_ws(" ",
                                  case
                                      when
                                          cl36.formation_age_Ma is not null
                                          then concat_ws(" ",
                                                         name,
                                                         coalesce(aliquot,""),
                                                         "formation_age_Ma", 
                                                         coalesce(truncate(formation_age_Ma, 3), 0),
                                                         coalesce(truncate(delformation_age_Ma, 3), 0),
                                                         ";"
                                          )
                                      else "" end
                        )
                SEPARATOR ' ') as formation_age_text
         from sample s
                  left join _cl36 cl36 on s.id = cl36.sample_id
         group by s.id
     ),
     major_text as (
                select s.id,
                group_concat(
                        concat_ws(" ",
                                  case when LOI_pct_wt is not null
                                        or H_pct_wt is not null
                                        or C_pct_wt is not null
                                        or O_pct_wt is not null
                                        or Na_pct_wt is not null
                                        or Mg_pct_wt is not null
                                        or Al_pct_wt is not null
                                        or Si_pct_wt is not null
                                        or P_pct_wt is not null
                                        or S_pct_wt is not null
                                        or K_pct_wt is not null
                                        or Ca_pct_wt is not null
                                        or Ti_pct_wt is not null
                                        or Mn_pct_wt is not null
                                        or Fe_pct_wt is not null
                                        or delCa_pct_wt is not null
                                        or delFe_pct_wt is not null
                                        or delK_pct_wt is not null
                                        or delTi_pct_wt is not null
                                  then
                                      concat_ws(" ",
                                        s.name,
                                        coalesce(aliquot,""),
                                        "major_elements", 
                                        majorel.what,
                                        coalesce(concat("LOI ", round(LOI_pct_wt, 2)), ""),
                                        coalesce(concat("H ", round(H_pct_wt, 2)), ""),
                                        coalesce(concat("C ", round(C_pct_wt, 2)), ""),
                                        coalesce(concat("O ", round(O_pct_wt, 2)), ""),
                                        coalesce(concat("Na ", round(Na_pct_wt, 2)), ""),
                                        coalesce(concat("Mg ", round(Mg_pct_wt, 2)), ""),
                                        coalesce(concat("Al ", round(Al_pct_wt, 2)), ""),
                                        coalesce(concat("Si ", round(Si_pct_wt, 2)), ""),
                                        coalesce(concat("P ", round(P_pct_wt, 2)), ""),
                                        coalesce(concat("S ", round(S_pct_wt, 2)), ""),
                                        coalesce(concat("K ", round(K_pct_wt, 2)), ""),
                                        coalesce(round(delK_pct_wt, 2), ""),
                                        coalesce(concat("Ca ", round(Ca_pct_wt, 2)), ""),
                                        coalesce(round(delCa_pct_wt, 2), ""),
                                        coalesce(concat("Ti ", round(Ti_pct_wt, 2)), ""),
                                        coalesce(round(delTi_pct_wt, 2), ""),
                                        coalesce(concat("Mn ", round(Mn_pct_wt, 2)), ""),
                                        coalesce(concat("Fe ", round(Fe_pct_wt, 2)), ""),
                                        coalesce(round(delFe_pct_wt, 2), ""),
                                        ";"
                                      )
                                  else ""
                                  end
                        )
                SEPARATOR ' ') as major_text
         from sample s
                  left join _major_element majorel on s.id = majorel.sample_id
         group by s.id
     ), trace_text as (
             select s.id,
                group_concat(
                        concat_ws(" ",
                                  case when
                                      Li_ppm is not null
                                      or B_ppm is not null
                                      or Cl_ppm is not null
                                      or Cr_ppm is not null
                                      or Co_ppm is not null
                                      or Sm_ppm is not null
                                      or Gd_ppm is not null
                                      or Th_ppm is not null
                                      or U_ppm is not null
                                      or delU_ppm is not null
                                      or delTh_ppm is not null
                                  then
                                      concat_ws(" ",
                                        s.name,
                                        coalesce(aliquot,""),
                                        "trace_elements",
                                        coalesce(concat("Li ", round(Li_ppm, 1)), ""),
                                        coalesce(concat("B ", round(B_ppm, 1)), ""),
                                        coalesce(concat("Cl ", round(Cl_ppm, 1)), ""),
                                        coalesce(concat("Cr ", round(Cr_ppm, 1)), ""),
                                        coalesce(concat("Co ", round(Co_ppm, 1)), ""),
                                        coalesce(concat("Sm ", round(Sm_ppm, 1)), ""),
                                        coalesce(concat("Gd ", round(Gd_ppm, 1)), ""),
                                        coalesce(concat("Th ", round(Th_ppm, 1)), ""),
                                        coalesce(round(delTh_ppm, 1), ""),
                                        coalesce(concat("U ", round(U_ppm, 1)), ""),
                                        coalesce(round(delU_ppm, 1), ""),
                                        ";"
                                      )
                                  else ""
                                  end
                        )
                SEPARATOR ' ') as trace_text
         from sample s
                  left join _trace_element traceel on s.id = traceel.sample_id
         group by s.id
)
select st.id,
       st.name,
       case when cl36.cl36_text REGEXP ';' or fat.formation_age_text REGEXP ';' or majorel.major_text REGEXP ';' or traceel.trace_text REGEXP ';'
       then
            concat_ws("\n", st.sample_text, cl36.cl36_text, fat.formation_age_text, majorel.major_text, traceel.trace_text)
       else ""
       end as output
from sample_text st
         left join cl36_text cl36 on st.id = cl36.id
         left join formation_age_text fat on st.id = fat.id
         left join major_text majorel on st.id = majorel.id
         left join trace_text traceel on st.id = traceel.id;
"""


def sample_nuclide_match_query(sample_ids: list[int], core_samples=False):
    if core_samples:
        return f"""
with coresamples as (
    select * from base_coresample
    where id in ({','.join([str(id_val) for id_val in sample_ids])})
)
select cs.id,
       cs.name,
       cs.top_depth_cm,
       cs.bot_depth_cm,
       cs.top_depth_gcm2,
       cs.bot_depth_gcm2,
       cs.measured_density,
       cs.lithology,
       cs.comments,
       count(distinct be10_al26_quartz.N10_atoms_g) as be10_n10_atoms_count,
       count(distinct be10_al26_quartz.N26_atoms_g) as be10_n26_atoms_count,
       count(distinct c14_quartz.N14_atoms_g) as c14_n14_atoms_count,
       count(distinct he3_quartz.N3c_atoms_g) as he3quart_n3c_atoms_count,
       count(distinct he3_pxol.N3c_atoms_g) as he3pxol_n3c_atoms_count,
       count(distinct ne21_quartz.N21xs_atoms_g) as ne21_n21xs_atoms_count,
       count(cl36.id) as cl36_count
from coresamples cs
    left join base_coresamplenuclidematch cc on cs.id = cc.coresample_id
    left join _be10_al26_quartz be10_al26_quartz on cc.Be10_Al26_quartz_id = be10_al26_quartz.id
    left join _c14_quartz c14_quartz on cc.C14_quartz_id = c14_quartz.id
    left join _he3_quartz he3_quartz on cc.He3_quartz_id = he3_quartz.id
    left join _he3_pxol he3_pxol on cc.He3_pxol_id = he3_pxol.id
    left join _ne21_quartz ne21_quartz on cc.Ne21_quartz_id = ne21_quartz.id
    left join _cl36 cl36 on cc.Cl36_id = cl36.id
group by cs.id;
"""
    else:
        return f"""
select s.id,
           s.name,
           s.lat_DD,
           s.lon_DD,
           s.elv_m,
           s.lithology,
           s.what,
           st.short_name as site_short_name,
           count(distinct be10_al26_quartz.N10_atoms_g) as be10_n10_atoms_count,
           count(distinct be10_al26_quartz.N26_atoms_g) as be10_n26_atoms_count,
           count(distinct c14_quartz.N14_atoms_g) as c14_n14_atoms_count,
           count(distinct he3_quartz.N3c_atoms_g) as he3quart_n3c_atoms_count,
           count(distinct he3_pxol.N3c_atoms_g) as he3pxol_n3c_atoms_count,
           count(distinct ne21_quartz.N21xs_atoms_g) as ne21_n21xs_atoms_count,
           count(cl36.id) as cl36_count
from base_sample s
     left join base_site st on st.id = s.site_id
     left join _be10_al26_quartz be10_al26_quartz on s.id = be10_al26_quartz.sample_id
     left join _c14_quartz c14_quartz on s.id = c14_quartz.sample_id
     left join _he3_quartz he3_quartz on s.id = he3_quartz.sample_id
     left join _he3_pxol he3_pxol on s.id = he3_pxol.sample_id
     left join _ne21_quartz ne21_quartz on s.id = ne21_quartz.sample_id
     left join _cl36 cl36 on s.id = cl36.sample_id
where s.id in ({','.join([str(id_val) for id_val in sample_ids])})
group by s.id    
"""


# This comes back as a JSON payload - easier to convert to API later + sorted already
def depth_nuclide_concentration_query(core_id):
    return f"""
    with core_samples as (
    select ccs.id as ccs_id,
           ccs.top_depth_cm,
           ccs.bot_depth_cm,
           ccs.top_depth_gcm2,
           ccs.bot_depth_gcm2,
           N21xs_atoms_g,
           delN21xs_atoms_g,
           Ne21_quartz_id,
           N10_atoms_g,
           delN10_atoms_g,
           Be10_Al26_quartz_id,
           N26_atoms_g,
           delN26_atoms_g
    from base_coresample ccs
    left join base_coresamplenuclidematch ccsnm on ccsnm.coresample_id = ccs.id
    left join _ne21_quartz n21q on ccsnm.Ne21_quartz_id = n21q.id
    left join _be10_al26_quartz b10a26 on ccsnm.Be10_Al26_quartz_id = b10a26.id
    where ccs.core_id = {core_id}
), ne21_data as (
    select
       min(ccs.top_depth_cm) as top_depth_cm,
       max(ccs.bot_depth_cm) as bot_depth_cm,
       min(ccs.top_depth_gcm2) as top_depth_gcm2,
       max(ccs.bot_depth_gcm2) as bot_depth_gcm2,
       N21xs_atoms_g,
       delN21xs_atoms_g,
       count(Ne21_quartz_id) as count
    from core_samples ccs
    where N21xs_atoms_g > 0
    group by Ne21_quartz_id
    order by top_depth_cm
), be10_data as (
    select
       min(ccs.top_depth_cm) as top_depth_cm,
       max(ccs.bot_depth_cm) as bot_depth_cm,
       min(ccs.top_depth_gcm2) as top_depth_gcm2,
       max(ccs.bot_depth_gcm2) as bot_depth_gcm2,
       N10_atoms_g,
       delN10_atoms_g,
       count(Be10_Al26_quartz_id) as count
    from core_samples ccs
    where N10_atoms_g > 0
    group by Be10_Al26_quartz_id
    order by top_depth_cm
), al26_data as (
    select
       min(ccs.top_depth_cm) as top_depth_cm,
       max(ccs.bot_depth_cm) as bot_depth_cm,
       min(ccs.top_depth_gcm2) as top_depth_gcm2,
       max(ccs.bot_depth_gcm2) as bot_depth_gcm2,
       N26_atoms_g,
       delN26_atoms_g,
       count(Be10_Al26_quartz_id) as count
    from core_samples ccs
    where N26_atoms_g > 0
    group by Be10_Al26_quartz_id
    order by top_depth_cm
), ne21_json as (
    select JSON_ARRAYAGG(
    JSON_OBJECT(
        'top_depth_cm', top_depth_cm,
        'bot_depth_cm', bot_depth_cm,
        'top_depth_gcm2', top_depth_gcm2,
        'bot_depth_gcm2', bot_depth_gcm2,
        'n21_atoms_g', N21xs_atoms_g,
        'deln21_atoms_g', delN21xs_atoms_g,
        'count', count
    )) from ne21_data
    order by top_depth_cm
), be10_json as (
    select JSON_ARRAYAGG(
    JSON_OBJECT(
        'top_depth_cm', top_depth_cm,
        'bot_depth_cm', bot_depth_cm,
        'top_depth_gcm2', top_depth_gcm2,
        'bot_depth_gcm2', bot_depth_gcm2,
        'n10_atoms_g', N10_atoms_g,
        'deln10_atoms_g', delN10_atoms_g,
        'count', count
    )) from be10_data
    order by top_depth_cm
), al26_json as (
    select JSON_ARRAYAGG(
    JSON_OBJECT(
        'top_depth_cm', top_depth_cm,
        'bot_depth_cm', bot_depth_cm,
        'top_depth_gcm2', top_depth_gcm2,
        'bot_depth_gcm2', bot_depth_gcm2,
        'n26_atoms_g', N26_atoms_g,
        'deln26_atoms_g', delN26_atoms_g,
        'count', count
    )) from al26_data
    order by top_depth_cm
) select JSON_OBJECT(
    'Be-10 (qtz)', (select * from be10_json),
    'Ne-21 (qtz)', (select * from ne21_json),
    'Al-26 (qtz)', (select * from al26_json)
)
"""
