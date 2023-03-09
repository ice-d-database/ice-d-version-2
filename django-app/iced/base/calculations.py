import os
import xml.etree.ElementTree as ET

import requests


def xml_to_form_v3(xml_data, all_sample_mapped):
    # Create dict to match XML fields to nuclide ID
    d_actelv = all_sample_mapped["d_elv"]
    d_iceelv = all_sample_mapped["d_surfelv"]
    d_what = all_sample_mapped["d_what"]
    nmatch = {
        "t3quartz_LSDn": "t3q",
        "t3olivine_LSDn": "t3op",
        "t3pyroxene_LSDn": "t3op",
        "t10quartz_LSDn": "t10q",
        "t14quartz_LSDn": "t14q",
        "t21quartz_LSDn": "t21q",
        "t26quartz_LSDn": "t26q",
    }

    if "<calcs_v3_age_data>" in xml_data:
        # Case is the appropriate XML object
        # Parse
        xml_tree = ET.fromstring(xml_data)

        # Initialize
        s_sname = ""
        s_actelv = ""
        s_iceelv = ""
        s_nname = ""
        s_t = ""
        s_dtint = ""
        s_dtext = ""
        s_what = ""

        for age in xml_tree.iter("exposureAgeResult"):

            # Now iterate
            # Each "age" for a sample has 19 fields -- one field for sample
            # name at beginning, followed by six for each scaling method.
            numages = int((len(age) - 1) / 18)
            # This will break if there aren't the correct multiple of fields.
            # Also might break if there are fields that aren't in dicts above.
            for i in range(1, (numages + 1)):
                startindex = (i - 1) * 18 + 13
                # Line above is to use 'LSDn' scaling. For 'St' use + 1 instead of + 7.
                nid = age[startindex].tag
                if nid in nmatch:
                    # Sample name, all rows
                    this_sname = age[0].text
                    s_sname += f"{this_sname} "
                    # Nuclide identifier
                    s_nname += f"{nmatch[nid]} "
                    # Elevations
                    if d_actelv[this_sname] is not None:
                        s_actelv += f"{d_actelv[this_sname]:0.0f} "
                    else:
                        s_actelv += "-1 "
                    if d_iceelv[this_sname] is not None:
                        s_iceelv += f"{d_iceelv[this_sname]:0.0f} "
                    else:
                        s_iceelv += "-1 "
                    # What
                    if ("Bedrock" in d_what[this_sname]) or (
                        "bedrock" in d_what[this_sname]
                    ):
                        s_what += "BR "
                    elif ("Erratic" in d_what[this_sname]) or (
                        "erratic" in d_what[this_sname]
                    ):
                        s_what += "ERR "
                    else:
                        s_what += "UNK "
                    # Age
                    s_t += f"{age[startindex].text} "
                    s_dtint += f"{age[startindex + 1].text} "
                    s_dtext += f"{age[startindex + 2].text} "
        formatted_xml_data = {
            "s_sname": s_sname,
            "s_actelv": s_actelv,
            "s_iceelv": s_iceelv,
            "s_what": s_what,
            "s_nname": s_nname,
            "s_t": s_t,
            "s_dtint": s_dtint,
            "s_dtext": s_dtext,
        }
        return formatted_xml_data
    else:
        return {}


def format_xml_data(xml_data):
    nmatch1 = {
        "t3quartz_St": "He-3 (qtz)",
        "t3olivine_St": "He-3 (ol)",
        "t3pyroxene_St": "He-3 (px)",
        "t10quartz_St": "Be-10 (qtz)",
        "t14quartz_St": "C-14 (qtz)",
        "t21quartz_St": "Ne-21 (qtz)",
        "t26quartz_St": "Al-26 (qtz)",
        "t36_St": "Cl-36",
    }
    nmatch2 = {
        "t3quartz_LSDn": "He-3 (qtz)",
        "t3olivine_LSDn": "He-3 (ol)",
        "t3pyroxene_LSDn": "He-3 (px)",
        "t10quartz_LSDn": "Be-10 (qtz)",
        "t14quartz_LSDn": "C-14 (qtz)",
        "t21quartz_LSDn": "Ne-21 (qtz)",
        "t26quartz_LSDn": "Al-26 (qtz)",
        "t36_LSDn": "Cl-36",
    }
    all_st_age_data = []
    all_lsdn_age_data = []
    all_plot_names = []
    diagnostics_text = ""
    if "<calcs_v3_age_data>" in xml_data:
        xml_tree = ET.fromstring(xml_data)
        for age in xml_tree.iter("exposureAgeResult"):
            numages = int((len(age) - 1) / 3)
            for i in range(1, (numages + 1)):
                startindex = (i - 1) * 3 + 1
                nid = age[startindex].tag
                if nid in nmatch1:
                    st_age_data = {
                        "sample_name": age[0].text,
                        "nuclide_id": nmatch1[nid],
                        "age": age[startindex].text,
                        "interr": age[startindex + 1].text,
                        "exterr": age[startindex + 2].text,
                    }
                    all_st_age_data.append(st_age_data)

        for age in xml_tree.iter("exposureAgeResult"):
            numages = int((len(age) - 1) / 3)
            for i in range(1, (numages + 1)):
                startindex = (i - 1) * 3 + 1
                nid = age[startindex].tag
                if nid in nmatch2:
                    lsdn_age_data = {
                        "sample_name": age[0].text,
                        "nuclide_id": nmatch2[nid],
                        "age": age[startindex].text,
                        "interr": age[startindex + 1].text,
                        "exterr": age[startindex + 2].text,
                    }
                    all_lsdn_age_data.append(lsdn_age_data)

        for plot_name in xml_tree.iter("ploturlstub"):
            all_plot_names.append(plot_name)

        diagnostics_text = (
            xml_tree.find("diagnostics")
            .text.replace("....", ".\n")
            .replace("...", "\n")
        )

        textSt = ""
        textLSDn = ""
        camel_plot = None
        summary_data = xml_tree.findall("summary")
        if len(summary_data) > 0:
            summary_data = summary_data[0]
            stSt = summary_data.findall("./all/St/text")[0]
            textSt = stSt.text.replace("...", "\n")
            textSt = textSt.replace("\n.", ".\n")
            stLSDn = summary_data.findall("./all/LSDn/text")[0]
            textLSDn = stLSDn.text.replace("...", "\n")
            textLSDn = textLSDn.replace("\n.", ".\n")

            camel_plot = xml_tree.findall("camelploturlstubs")
            if len(camel_plot) > 0:
                camel_plot = camel_plot[0]

        formatted_xml_data = {
            "all_st_age_data": all_st_age_data,
            "all_lsdn_age_data": all_lsdn_age_data,
            "all_plot_names": all_plot_names,
            "diagnostics_text": diagnostics_text,
            "camel_plots": camel_plot,
            "textSt": textSt,
            "textLSDn": textLSDn,
        }
        return formatted_xml_data

    else:
        return {}


def get_Cl36_ages_v3(s, summary):
    # arg s is the text string to send to the calculator...
    # assemble form data
    form_fields = {
        "mlmfile": "Cl36_input_v3",
        "reportType": "XML",
        "summary": summary,
        "plotFlag": "yes",
        "text_block": s,
    }

    if os.getenv("SERVER_SOFTWARE") and os.getenv("SERVER_SOFTWARE").startswith(
        "Google App Engine/"
    ):
        full_url = "http://stoneage.ice-d.org/cgi-bin/matweb"
    else:
        # TODO switch this back to local
        # full_url = "http://192.168.56.101/cgi-bin/matweb"
        full_url = "http://stoneage.ice-d.org/cgi-bin/matweb"

    response = requests.post(full_url, data=form_fields)
    response_text = response.text
    return response_text


def get_ages_v3(calculation_text):
    """Input v3 data into calculator and get output"""
    # TODO: This is from legacy_dbs code, I think this will be replaced
    form_fields = {
        "mlmfile": "age_input_v3",
        "reportType": "XML",
        "resultType": "long",
        "plotFlag": "yes",
        "text_block": calculation_text,
        # "summary" : "yes", # This has to be switched depending on site type -- ?
    }

    if os.getenv("SERVER_SOFTWARE") and os.getenv("SERVER_SOFTWARE").startswith(
        "Google App Engine/"
    ):
        full_url = "http://hess.ess.washington.edu/cgi-bin/matweb"
        # full_url = "http://stoneage.ice-d.org/cgi-bin/matweb"
    else:
        # Local VM on GB's laptop
        # TODO switch this back to local
        # full_url = "http://192.168.56.101/cgi-bin/matweb"
        full_url = "http://hess.ess.washington.edu/cgi-bin/matweb"

    response = requests.post(full_url, data=form_fields)
    response_text = response.text
    return response_text
