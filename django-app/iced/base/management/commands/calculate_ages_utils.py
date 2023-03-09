import json
import logging

from base.models import CalculatedAge, Sample

def make_single_nuclide_fields_map(name, nnorm_name=None):
    map = {
        "t_St": f"{name}_St",
        "dtint_St": f"del{name}_int_St",
        "dtext_St": f"del{name}_ext_St",
        "t_Lm": f"{name}_Lm",
        "dtint_Lm": f"del{name}_int_Lm",
        "dtext_Lm": f"del{name}_ext_Lm",
        "t_LSDn": f"{name}_LSDn",
        "dtint_LSDn": f"del{name}_int_LSDn",
        "dtext_LSDn": f"del{name}_ext_LSDn"
    }

    nnorm_map = {} if nnorm_name is None else {
        "Nnorm_St": f"Nnorm{nnorm_name}_St",
        "dNnorm_St": f"delNnorm{nnorm_name}_int_St",
        "dNnorm_ext_St": f"delNnorm{nnorm_name}_ext_St",
        "Nnorm_Lm": f"Nnorm{nnorm_name}_Lm",
        "dNnorm_Lm": f"delNnorm{nnorm_name}_int_Lm",
        "dNnorm_ext_Lm": f"delNnorm{nnorm_name}_ext_Lm",
        "Nnorm_LSDn": f"Nnorm{nnorm_name}_LSDn",
        "dNnorm_LSDn": f"delNnorm{nnorm_name}_int_LSDn",
        "dNnorm_ext_LSDn": f"delNnorm{nnorm_name}_ext_LSDn",
    }

    return {**map, **nnorm_map}

nuclide_maps = {
    "t3quartz_St": {
        "nuclide": "N3quartz",
        "fields": make_single_nuclide_fields_map('t3quartz', nnorm_name='3quartz')
    },
    "t3olivine_St": {
        "nuclide": "N3olivine",
        "fields": make_single_nuclide_fields_map('t3olivine', nnorm_name='3olivine')
    },
    "t3pyroxene_St": {
        "nuclide": "N3pyroxene",
        "fields": make_single_nuclide_fields_map('t3pyroxene', nnorm_name='3pyroxene')
    },
    "t10quartz_St": {
        "nuclide": "N10quartz",
        "fields": make_single_nuclide_fields_map('t10quartz', nnorm_name='10quartz')
    },
    "t14quartz_St": {
        "nuclide": "N14quartz",
        "fields": make_single_nuclide_fields_map('t14quartz', nnorm_name='14quartz')
    },
    "t21quartz_St": {
        "nuclide": "N21quartz",
        "fields": make_single_nuclide_fields_map('t21quartz', nnorm_name='21quartz')
    },
    "t26quartz_St": {
        "nuclide": "N26quartz",
        "fields": make_single_nuclide_fields_map('t26quartz', nnorm_name='26quartz')
    },
    "t36_St" : {
        "nuclide": "t36",
        "fields": make_single_nuclide_fields_map('t36')
    }
}


def parse_and_insert(calculatedResults, sample_id):
    ages = json.loads(calculatedResults)[0][1]["exposureAgeResult"]
    count = 0
    for nuclide in nuclide_maps:
        if nuclide in ages:
            fields = nuclide_maps[nuclide]['fields']
            nuclide_value = nuclide_maps[nuclide]['nuclide']
            records_to_load = []
            for field in fields:
                ages_field = fields[field]
                value = ages[ages_field]
                value = value if value != 'NaN' else None
                # If we have a list, we have multiple records that need to be generated
                if isinstance(value, list):
                   if len(records_to_load) == 0:
                       [records_to_load.append({'nuclide': nuclide_value, 'sample_id': sample_id})
                        for x in range(len(value))]
                   for i, v in enumerate(value):
                       records_to_load[i][field] = v
                else:
                    if len(records_to_load) == 0:
                        records_to_load.append({'nuclide': nuclide_value, 'sample_id': sample_id})
                    records_to_load[0][field] = value
            print(records_to_load[0])
            for r in records_to_load:
                calc_age = CalculatedAge(**r)
                calc_age.save()
                count+=1
    return count