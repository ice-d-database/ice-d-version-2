import json
import logging
import statistics

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import HttpResponse
from django.template import loader

from .plots import age_elevation_plot, camelplot, NofZplot

from .models import (
    Application,
    Calculation,
    CalibrationData,
    Continent,
    Core,
    CoreSample,
    CoresampleNuclideMatch,
    FieldProperName,
    Project,
    Publication,
    Sample,
    SamplePublicationsMatch,
    Site,
    Be10Al26Quartz,
    C14Quartz,
    He3Quartz,
    He3Pxol,
    Ne21Quartz,
    UThQuartz,
    Cl36,
    MajorElement,
    TraceElement,
)

logger = logging.getLogger(__name__)

context_base = {
    "name_string": "",
    "header_img_path": "img/star_image.jpg",
    "header_table_attr": "",
    "header_info": "",
    "footer_credits": "",
}


def _call_calculation(calculation_name: str, input: str):
    calculation = Calculation.get_calculation_by_name(calculation_name)
    variables = json.loads(calculation.variable_json)
    variables["summary"] = "no"
    variables["text_block"] = input
    run_calculation_endpoint = (
        f"{settings.BASE_URL}/api/calculations/run/" + calculation_name
    )

    req = requests.request("GET", run_calculation_endpoint, data=json.dumps(variables))
    if req.status_code != 200:
        return ""
    else:
        return req.text


def _format_calc_string(str):
    lines = [' '.join(l.strip().split()) for l in str.split(';')]
    lines = list(filter(lambda line: len(line) > 0, lines))
    return ';\n'.join(lines) + ";" if len(lines) > 0 else ''


def _rename_age_results(results):
    # Takes calculation results and returns exposure age data to be presented on page
    St_match = {
        "t3quartz_St": "He-3 (qtz)",
        "t3olivine_St": "He-3 (ol)",
        "t3pyroxene_St": "He-3 (px)",
        "t10quartz_St": "Be-10 (qtz)",
        "t14quartz_St": "C-14 (qtz)",
        "t21quartz_St": "Ne-21 (qtz)",
        "t26quartz_St": "Al-26 (qtz)",
        "t36_St": "Cl-36",
    }
    LSD_match = {
        "t3quartz_LSDn": "He-3 (qtz)",
        "t3olivine_LSDn": "He-3 (ol)",
        "t3pyroxene_LSDn": "He-3 (px)",
        "t10quartz_LSDn": "Be-10 (qtz)",
        "t14quartz_LSDn": "C-14 (qtz)",
        "t21quartz_LSDn": "Ne-21 (qtz)",
        "t26quartz_LSDn": "Al-26 (qtz)",
        "t36_LSDn": "Cl-36",
    }

    if isinstance(results, dict):
        results = [results]
    exposure_age_table_data = {}

    for result in results:
        keys = list(result)  # Get list of keys
        for i, r in enumerate(result):
            for m in St_match:
                if m in r:
                    sample_name = result["sample_name"]
                    if sample_name not in exposure_age_table_data:
                        exposure_age_table_data[sample_name] = {}
                    if "St" not in exposure_age_table_data[sample_name]:
                        exposure_age_table_data[sample_name]["St"] = {}

                    if isinstance(result[keys[i]], list):
                        exposure_age_table_data[sample_name]["St"][St_match[m]] = [
                            list(v)
                            for v in zip(
                                result[keys[i]],
                                result[keys[i + 1]],
                                result[keys[i + 2]],
                            )
                        ]
                    else:
                        exposure_age_table_data[sample_name]["St"][St_match[m]] = [
                            [result[keys[i]], result[keys[i + 1]], result[keys[i + 2]]]
                        ]

            for m in LSD_match:
                if m in r:
                    sample_name = result["sample_name"]
                    if sample_name not in exposure_age_table_data:
                        exposure_age_table_data[sample_name] = {}
                    if "LSD" not in exposure_age_table_data[sample_name]:
                        exposure_age_table_data[sample_name]["LSD"] = {}
                    if isinstance(result[keys[i]], list):
                        exposure_age_table_data[sample_name]["LSD"][LSD_match[m]] = [
                            list(v)
                            for v in zip(
                                result[keys[i]],
                                result[keys[i + 1]],
                                result[keys[i + 2]],
                            )
                        ]
                    else:
                        exposure_age_table_data[sample_name]["LSD"][LSD_match[m]] = [
                            [result[keys[i]], result[keys[i + 1]], result[keys[i + 2]]]
                        ]
    return exposure_age_table_data


def _get_calculated_age_plot_diagnostics(calc_str, calc_to_call):
    if calc_str != "":
        try:
            calculated = json.loads(_call_calculation(calc_to_call, calc_str))

            age_results = _rename_age_results(
                calculated[0][1]["exposureAgeResult"]
            )
            plots = (
                calculated[0][1]["ploturlstub"]
                if "ploturlstub" in calculated[0][1]
                else []
            )
            diagnostics = (
                calculated[0][1]["diagnostics"]
                if "diagnostics" in calculated[0][1]
                else []
            )
        except:
            age_results = plots = diagnostics = []
    else:
        age_results = plots = diagnostics = []

    if isinstance(plots, str):
        plots = [plots]

    return age_results, plots, diagnostics


def error_404_page(not_found: str, request) -> HttpResponse:
    logger.error(f"404 - {request.path}")
    template_404 = loader.get_template("404.html")
    context_404 = {"not_found": not_found} | context_base
    return HttpResponse(template_404.render(context_404, request))


def home(request):
    applications = Application.objects.all()

    context = {
        "applications": applications,
        "header_img_path": "img/star_image.jpg",
    }

    template = loader.get_template("home.html")
    return HttpResponse(template.render(context, request))


def landing(request, application_name):
    application_name = application_name.lower()
    try:
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(f"Can't find an application: {application_name}", request)
    distinct_contintents = Site.get_distinct_continents_by_application(application)
    publication_count = Publication.get_publication_count_by_application(application)
    site_ids = Site.get_site_ids_by_application(application)
    core_count = Core.get_core_count_by_sites(site_ids)
    show_all_cores = core_count > 0
    show_publications = publication_count > 0
    show_pubyears = publication_count > 0

    browse_by_site_list = (
        [
            {
                "name": c,
                "url": "sites/" + c.lower(),
            }
            for c in distinct_contintents
        ]
        if len(distinct_contintents) > 1
        else []
    )

    context = {
        "browse_by_site_list": browse_by_site_list,
        "show_all_cores": show_all_cores,
        "show_publications": show_publications,
        "show_pubyears": show_pubyears,
        "google_map_key": settings.GOOGLE_MAP_API_KEY,
    } | application.get_application_ctx()

    template = loader.get_template("application.html")

    return HttpResponse(template.render(context, request))


def cores(request, application_name):
    application_name = application_name.lower()

    try:
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(f"Can't find application: {application_name}", request)

    sites = application.sites.all().prefetch_related("cores").select_related("region")

    cores_by_site = [
        {"cores": site.cores.all(), "site": site}
        for site in sites
        if len(site.cores.all()) > 0
    ]

    context = {
        "page_title": "Cores and subsurface data",
        "cores_by_site": cores_by_site,
    } | application.get_application_ctx()

    template = loader.get_template("cores.html")
    return HttpResponse(template.render(context, request))


def sitemap(request, application_name, site, lat, lon, zoom):
    application_name = application_name.lower()

    try:
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(f"Can't find application: {application_name}", request)

    context = {
        "page_title": f"Sitemap for " + site,
        "google_map_key": settings.GOOGLE_MAP_API_KEY,
    } | application.get_application_ctx()

    template = loader.get_template("sitemap.html")
    return HttpResponse(template.render(context, request))


def core(request, application_name, core_name):
    application_name = application_name.lower()
    core_name = core_name.lower()
    try:
        core_obj = Core.get_core_by_name(core_name)
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application/base: {application_name}, {core_name}", request
        )

    core_samples = core_obj.get_all_core_samples()

    core_sample_ids = [core_sample.id for core_sample in core_samples]

    publications_match = SamplePublicationsMatch.get_publications_by_core_sample_ids(
        core_sample_ids
    )
    # MySQL doesn't support `DISTINCT ON` so uniquifying here using set
    publications = set([pm.publication for pm in publications_match])
    n_tables = CoreSample.get_formatted_nuclide(core_sample_ids)
    depth_nuclide_data = json.loads(core_obj.get_depth_nuclide_concentration())

    [plot_script, plot_div] = NofZplot(depth_nuclide_data)
    if len(plot_script) > 0:
        is_NofZ_plot=True
    else:
        is_NofZ_plot=False


    context = {
        "page_title": f"Samples From core <em>{core_obj.name}</em> ({ core_obj.description })",
        "core": core_obj,
        "publications": publications,
        "core_samples": core_samples,
        "n_tables": n_tables,
        "depth_nuclide_data": depth_nuclide_data,
        "plot_script": plot_script,
        "plot_div": plot_div.replace('<div','<div style="display:flex; align-items:center; justify-content:center;"'),
        "is_NofZ_plot": is_NofZ_plot
    } | application.get_application_ctx()

    template = loader.get_template("core.html")
    return HttpResponse(template.render(context, request))


def coresample(request, application_name, coresample_name):
    application_name = application_name.lower()
    coresample_name = coresample_name.lower()
    try:
        coresample_obj = CoreSample.get_core_sample_by_name(coresample_name)
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application/sample: {application_name}, {coresample_name}",
            request,
        )

    field_proper_names = application.get_sample_field_proper_names_dict()

    db_ntables = CoresampleNuclideMatch.get_nuclide_match_data(coresample_obj)
    ntables = []

    for ntable in db_ntables:
        for fpn in field_proper_names:
            try:
                record = getattr(ntable, fpn)
            except:
                record = None
            if record:
                ntables.append({"nuclide": fpn, "properties": record})
                break

    context = {
        "page_title": f"Comprehensive data dump for sample: {coresample_obj.name}",
        "coresample": coresample_obj,
        "field_proper_names": field_proper_names,
        "ntables": ntables,
    } | application.get_application_ctx()

    template = loader.get_template("coresample.html")
    return HttpResponse(template.render(context, request))


def publications(request, application_name):
    application_name = application_name.lower()
    try:
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application id: {application_name}", request
        )

    # The below uses a raw SQL query to get applications by going through sample pub matches.
    # Note also should go through site-core-coresample-pub matches.

    publications_spm = Publication.get_by_application(application)
    publication_ids = [p.publication.id for p in publications_spm]
    publications = Publication.objects.filter(id__in=publication_ids)

    counts = {}
    for m in publications_spm:
        pub_id_str = f"{m.publication_id}"
        if pub_id_str not in counts:
            counts[pub_id_str] = 0
        counts[pub_id_str] = counts[pub_id_str] + 1

    # Todo: There is a bug in the data loading where it's missing some associated samples with publications
    # we need to pin down. Otherwise this mostly works.
    context = {
        "page_title": "All publications",
        "publications": publications,
        "counts": counts,
    } | application.get_application_ctx()

    template = loader.get_template("publications.html")
    return HttpResponse(template.render(context, request))


def pubYears(request, application_name):
    application_name = application_name.lower()
    try:
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application id: {application_name}", request
        )


    publications = Publication.get_by_application(application)
    publication_ids = [p.publication.id for p in publications]

    publications_aggregate = (
        Publication.objects.all()
        .filter(id__in=publication_ids)
        .values("year")
        .annotate(total=Count("id"))
        .order_by("year")
        .values("year", "total")
    )

    context = {
        "page_title": "Browse publications by year",
        "publications": publications_aggregate,
    } | application.get_application_ctx()

    template = loader.get_template("pubyears.html")
    return HttpResponse(template.render(context, request))


def pubYear(request, application_name, year):
    application_name = application_name.lower()
    try:
        application = Application.get_application_by_name(application_name)
 
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application id: {application_name}", request
        )


    publications_spm = Publication.get_by_application(application)
    publication_ids = [p.publication.id for p in publications_spm]
    publications = Publication.objects.filter(id__in=publication_ids,year=year)

    match_records = SamplePublicationsMatch.objects.filter(
        publication_id__in=publication_ids ,publication__year=year, sample_id__isnull=False
    )
    counts = {}
    for m in match_records:
        pub_id_str = f"{m.publication_id}"
        if pub_id_str not in counts:
            counts[pub_id_str] = 0
        counts[pub_id_str] = counts[pub_id_str] + 1

    context = {
        "page_title": f"Publications dated {year}",
        "publications": publications,
        "counts": counts,
    } | application.get_application_ctx()

    template = loader.get_template("pubyear.html")
    return HttpResponse(template.render(context, request))


def nsf(request, application_name):
    application_name = application_name.lower()
    try:
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application id: {application_name}", request
        )

    projects = Project.objects.prefetch_related("funding_sources").filter(
        application=application, NSF_title__isnull=False
    )

    context = {
        "page_title": "NSF projects",
        "projects": projects,
    } | application.get_application_ctx()

    template = loader.get_template("nsf.html")
    return HttpResponse(template.render(context, request))


def nsf_samples(request, application_name, project_id):
    # Note: this doesn't appear to distinguish projects by application.
    # This will cause trouble if extended to applications other than Antarctica (e.g., Greenland).
    application_name = application_name.lower()
    try:
        application = Application.get_application_by_name(application_name)
        project_obj = Project.objects.prefetch_related(
            "funding_sources", "samples"
        ).get(pk=project_id)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application id or project: {application_name}, {project_id}",
            request,
        )
    sample_ids = [sample.id for sample in project_obj.samples.all()]
    n_tables = Sample.get_formatted_nuclide(sample_ids)

    no_cores = True
    cores = project_obj.cores.all()
    if len(cores) > 0:
        no_cores = False


    context = {
        "page_title": f"{project_obj.NSF_title}",
        "project": project_obj,
        "n_tables": n_tables,
        "no_cores": no_cores,
        "cores": cores,
    } | application.get_application_ctx()

    template = loader.get_template("nsf_samples.html")
    return HttpResponse(template.render(context, request))


def cal_data_set(request, application_name):
    try:
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application id: {application_name}", request
        )

    calibration_data_sets = (
        CalibrationData.objects.prefetch_related("samples")
        .select_related("publication")
        .all()
    )

    context = {
        "page_title": "Calibration data sets",
        "cal_data_sets": calibration_data_sets,
    } | application.get_application_ctx()

    template = loader.get_template("cal_data_set.html")
    return HttpResponse(template.render(context, request))


def cal_data_set_samples(request, application_name, cd_id):
    try:
        application = Application.get_application_by_name(application_name)
        cal_data_obj = (
            CalibrationData.objects.prefetch_related("samples")
            .select_related("publication")
            .get(pk=cd_id)
        )
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application id or calibration data set: {application_name}, {cd_id}",
            request,
        )

    sample_ids = [sample.id for sample in cal_data_obj.samples.all()]

    n_tables = Sample.get_formatted_nuclide(sample_ids)
    cl36_str = _format_calc_string(Sample.get_cl36_age_calc_string(sample_ids))
    v3_str = _format_calc_string(Sample.get_v3_age_calc_string(
        sample_ids, known_age=application.calibration_data_sets))

    # Note: at this point we need to trim the input text to not have nuclide concentration lines other than the
    # object of the calibration data set. Also differentiate between Cl-36/other.

    if cal_data_obj.nuclide != "Cl-36":
        cl36_str = ''
        # The following code removes all lines from the input text that don't pertain to the target
        # nuclide for this calibration data set.

        # possible nuclides
        possn = ['Be-10', 'Al-26', 'He-3', 'Ne-21', 'C-14']
        inlines = v3_str.splitlines()
        outtext = ''
        for thisline in inlines:
            ok = 1
            # First, check to see if it is a nuclide line
            words = thisline.split()
            if words[1] in possn:
                # is a nuclide line
                if cal_data_obj.nuclide == words[1]:
                    # is the correct nuclide, leave ok = 1
                    # However, check to make sure not He-3/quartz
                    if cal_data_obj.nuclide == 'He-3':
                        if words[2] == 'quartz':
                            ok = 0
                else:
                    # is not the correct nuclide
                    ok = 0

            # Now print if pass
            if ok == 1:
                outtext = outtext + thisline + "\n"

        v3_str = outtext

    if cal_data_obj.nuclide == "Cl-36":
        v3_str = ''

    context = {
        "page_title": f"Calibration data set: {cal_data_obj.name} ({cal_data_obj.nuclide})",
        "cal_data": cal_data_obj,
        "n_tables": n_tables,
        "v3_str": v3_str,
        "cl36_str": cl36_str,
        "publications": [cal_data_obj.publication],
    } | application.get_application_ctx()

    template = loader.get_template("cal_data_set_samples.html")
    return HttpResponse(template.render(context, request))


def publication(request, application_name, pub_id):
    application_name = application_name.lower()
    try:
        pub_obj = Publication.objects.get(pk=pub_id)
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application/publication id: {application_name}, {pub_id}",
            request,
        )

    samples = pub_obj.get_all_samples()
    sample_ids = [s.id for s in samples if s]
    if len(sample_ids) > 0:
        no_samples = False

        n_tables = Sample.get_formatted_nuclide(sample_ids)

        cl36_str = _format_calc_string(Sample.get_cl36_age_calc_string(sample_ids))
        v3_str = _format_calc_string(Sample.get_v3_age_calc_string(
            sample_ids, known_age=application.calibration_data_sets))
    else:
        n_tables = {}
        cl36_str = ""
        v3_str = ""
        no_samples = True

    cores = pub_obj.get_all_cores()

    no_cores = True
    if len(cores) > 0:
        no_cores = False


    context = {
        "page_title": f"Publication: {pub_obj.short_name}",
        "publication": pub_obj,
        "n_tables": n_tables,
        "cl36_str": cl36_str,
        "v3_str": v3_str,
        "no_samples": no_samples,
        "cores": cores,
    } | application.get_application_ctx()

    template = loader.get_template("publication.html")
    return HttpResponse(template.render(context, request))


def sites(request, application_name, continent=None):
    application_name = application_name.lower()
    try:
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(f"Can't find an application: {application_name}", request)

    sites = (
        application.sites.all()
        .select_related("region", "continent")
        .order_by("region__name", "sector")
    )

    if continent:
        sites = Site.get_sites_by_continent(application, continent)

    sites_by_region = {}
    for site in sites:
        if site.region.name not in sites_by_region:
            sites_by_region[site.region.name] = []
        sites_by_region[site.region.name].append(site)

    if continent:
        context = {
            "sites_by_region": sites_by_region,
            "page_title": f"{Continent.get_continent_name_by_slug(continent)} - {application.name}",
        } | application.get_application_ctx()
    else:
        context = {
            "sites_by_region": sites_by_region,
            "page_title": f"All sites - {application.name}",
        } | application.get_application_ctx()

    template = loader.get_template("sites.html")
    return HttpResponse(template.render(context, request))


def site(request, application_name, site_name):
    application_name = application_name.lower()
    try:
        application = Application.get_application_by_name(application_name)
        site_list = application.get_sites()
        site_obj = (
            Site.objects.filter(id__in=site_list)
            .select_related("region")
            .get(short_name__iexact=site_name)
        )
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application/site: {application_name}, {site_name}", request
        )

    samples = Sample.get_samples_by_site([site_obj.id])
    sample_ids = [sample.id for sample in samples]
    sample_lats = [sample.lat_DD for sample in samples]
    sample_lons = [sample.lon_DD for sample in samples]
    no_samples = False
    if len(sample_ids) > 0:
        publications = set(
            [
                spm.publication
                for spm in SamplePublicationsMatch.get_publications_by_sample_ids(
                    sample_ids
                )
            ]
        )

        n_tables = Sample.get_formatted_nuclide(sample_ids)
        cl36_str = _format_calc_string(Sample.get_cl36_age_calc_string(sample_ids))
        v3_str = _format_calc_string(Sample.get_v3_age_calc_string(
            sample_ids, known_age=application.calibration_data_sets))

        v3_age_results, v3_plots, v3_diagnostics = _get_calculated_age_plot_diagnostics(
            v3_str, "age_input_v3")
        cl36_age_results, cl36_plots, cl36_diagnostics = _get_calculated_age_plot_diagnostics(
            cl36_str, "Cl36_input_v3")

    else:
        # publications = []
        publications = set() # this has to be a set so it can be unioned later
        n_tables = {}
        cl36_str = ""
        v3_str = ""
        no_samples = True
        v3_age_results = []
        v3_plots = []
        v3_diagnostics = []
        cl36_age_results = []
        cl36_plots = []
        cl36_diagnostics = []

    cores = Core.get_cores_by_site([site_obj.id])
    core_ids = [core.id for core in cores]
    no_cores = False

    if len(core_ids) == 0:
        no_cores = True
    else:
        core_samples = CoreSample.get_core_samples_by_core(core_ids)
        core_sample_ids = [cs.id for cs in core_samples]
        publications_by_core_sample = set([
                spm.publication
                for spm in SamplePublicationsMatch.get_publications_by_core_sample_ids(
                    core_sample_ids
                )
            ]
        )
        publications = publications.union(publications_by_core_sample)
    # This triggers various summary plots for different site types.
    if site_obj.what is not None and 'unatak' in site_obj.what and (v3_age_results or cl36_age_results):
        # Case nunatak. Make age-elevation plot.
        sample_names = [sample.name for sample in samples]
        sample_whats = [sample.what for sample in samples]
        sample_elvs = [sample.elv_m for sample in samples]
        sample_ice = [sample.local_ice_surface_m for sample in samples]
        sample_dict = {"names": sample_names, "whats": sample_whats, "elvs": sample_elvs, "ice": sample_ice}
        [plot_script, plot_div] = age_elevation_plot(v3_age_results, cl36_age_results, sample_dict)
        is_summary_plot = True
        summary_plot_text = "Age-elevation plot (drag x-axis limit in upper plot)"
    elif (v3_age_results or cl36_age_results):
        # Case not a nunatak, but there are some data.
        # In this case, presumably landform has one age, so make a camel plot.
        sample_names = [sample.name for sample in samples]
        sample_whats = [sample.what for sample in samples]
        sample_dict = {"names": sample_names, "whats": sample_whats}
        is_summary_plot = True
        [plot_script, plot_div] = camelplot(v3_age_results, cl36_age_results, sample_dict)
        summary_plot_text = "Summary data"
        # Also do some summary stats?
    else:
        # No data, do nothing
        plot_script = ''
        plot_div = ''
        is_summary_plot = False
        summary_plot_text = ''



    context = {
        "site": site_obj,
        "samples": samples,
        "cores": cores,
        "publications": publications,
        "n_tables": n_tables,
        "v3_str": v3_str,
        "cl36_str": cl36_str,
        "v3_age_results": v3_age_results,
        "v3_plots": v3_plots,
        "v3_diagnostics": v3_diagnostics,
        "cl36_age_results": cl36_age_results,
        "cl36_plots": cl36_plots,
        "cl36_diagnostics": cl36_diagnostics,
        "no_samples": no_samples,
        "no_cores": no_cores,
        "avg_lat": statistics.mean(sample_lats) if len(sample_lats) > 0 else None,
        "avg_lon": statistics.mean(sample_lons) if len(sample_lons) > 0 else None,
        "page_title": f"Site { site_obj.short_name } ({ site_obj.region.name }, { site_obj.name })",
        "is_summary_plot": is_summary_plot,
        "summary_plot_text": summary_plot_text,
        "plot_script": plot_script,
        "plot_div": plot_div.replace('<div','<div style="display:flex; align-items:center; justify-content:center;"')
    } | application.get_application_ctx()

    template_site = loader.get_template("site.html")
    return HttpResponse(template_site.render(context, request))


def sample(request, application_name, sample_name):
    application_name = application_name.lower()
    sample_name = sample_name.lower()
    try:
        sample_obj = Sample.get_sample_by_name(sample_name)
        application = Application.get_application_by_name(application_name)
    except ObjectDoesNotExist:
        return error_404_page(
            f"Can't find an application/sample: {application_name}, {sample_name}",
            request,
        )

    n_tables = Sample.get_formatted_nuclide([sample_obj.id])
    v3_str = _format_calc_string(
        Sample.exposure_calculator_string_query([sample_obj.id]))
    cl36_str = _format_calc_string(Sample.cl36_calculator_string_query([sample_obj.id]))

    sampleTables = []
    albeTables = []
    c14qTables = []
    he3qTables = []
    he3pxolTables = []
    ne21qTables = []
    UThquartzTables = []
    cl36Tables = []
    majorTables = []
    traceTables = []

    sampleList = list()
    sampleQS = Sample.objects.filter(name=sample_obj.name)
    if len(sampleQS) > 0:
        for i in range(len(sampleQS)):
            sampleList.append(list(sampleQS.values())[i])

    albeList = list()
    albeQS = Be10Al26Quartz.objects.filter(sample_id=sample_obj.id)
    if len(albeQS) > 0:
        for i in range(len(albeQS)):
            albeList.append(list(albeQS.values())[i])

    c14qList = list()
    c14qQS = C14Quartz.objects.filter(sample_id=sample_obj.id)
    if len(c14qQS) > 0:
        for i in range(len(c14qQS)):
            c14qList.append(list(c14qQS.values())[i])

    he3qList = list()
    he3qQS = He3Quartz.objects.filter(sample_id=sample_obj.id)
    for i in range(len(he3qQS)):
        he3qList.append(list(he3qQS.values())[i])

    he3pxolList = list()
    he3pxolQS = He3Pxol.objects.filter(sample_id=sample_obj.id)
    for i in range(len(he3pxolQS)):
        he3pxolList.append(list(he3pxolQS.values())[i])

    ne21qList = list()
    ne21qQS = Ne21Quartz.objects.filter(sample_id=sample_obj.id)
    for i in range(len(ne21qQS)):
        ne21qList.append(list(ne21qQS.values())[i])

    UThquartzList = list()
    UThquartzQS = UThQuartz.objects.filter(sample_id=sample_obj.id)
    for i in range(len(UThquartzQS)):
        UThquartzList.append(list(UThquartzQS.values())[i])

    cl36List = list()
    cl36QS = Cl36.objects.filter(sample_id=sample_obj.id)
    for i in range(len(cl36QS)):
        cl36List.append(list(cl36QS.values())[i])

    majorList = list()
    majorQS = MajorElement.objects.filter(sample_id=sample_obj.id)
    for i in range(len(majorQS)):
        majorList.append(list(majorQS.values())[i])

    traceList = list()
    traceQS = TraceElement.objects.filter(sample_id=sample_obj.id)
    for i in range(len(traceQS)):
        traceList.append(list(traceQS.values())[i])

    sampleTables.clear()
    albeTables.clear()
    c14qTables.clear()
    he3qTables.clear()
    he3pxolTables.clear()
    ne21qTables.clear()
    UThquartzTables.clear()
    cl36Tables.clear()
    majorTables.clear()
    traceTables.clear()

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["base_sample"]

        for lst in sampleList:
            for item in lst:
                try:
                    sampleTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            sampleTables.append(" ")
    except:
        sampleTables.clear

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["be10_al26_quartz"]

        for lst in albeList:
            for item in lst:
                try:
                    albeTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            albeTables.append(" ")
    except:
        albeTables.clear

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["c14_quartz"]

        for lst in c14qList:
            for item in lst:
                try:
                    c14qTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            c14qTables.append(" ")
    except:
        c14qTables.clear

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["he3_quartz"]

        for lst in he3qList:
            for item in lst:
                try:
                    he3qTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            he3qTables.append(" ")
    except:
        he3qTables.clear

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["he3_pxol"]

        for lst in he3pxolList:
            for item in lst:
                try:
                    he3pxolTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            he3pxolTables.append(" ")
    except:
        he3pxolTables.clear

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["ne21_quartz"]

        for lst in ne21qList:
            for item in lst:
                try:
                    ne21qTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            ne21qTables.append(" ")
    except:
        ne21qTables.clear

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["u_th_quartz"]

        for lst in UThquartzList:
            for item in lst:
                try:
                    UThquartzTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            UThquartzTables.append(" ")
    except:
        UThquartzTables.clear

    for lst in UThquartzList:
        for item in lst:
            try:
                UThquartzTables.append(
                    {"key": proper_names[item][0], "value": lst[item]})
            except:
                continue
        UThquartzTables.append(" ")

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["cl36"]

        for lst in cl36List:
            for item in lst:
                try:
                    cl36Tables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            cl36Tables.append(" ")
    except:
        cl36Tables.clear

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["major_element"]

        for lst in majorList:
            for item in lst:
                try:
                    majorTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            majorTables.append(" ")
    except:
        majorTables.clear

    field_proper_names = application.get_sample_field_proper_names_dict()

    try:
        proper_names = field_proper_names["trace_element"]

        for lst in traceList:
            for item in lst:
                try:
                    traceTables.append(
                        {"key": proper_names[item][0], "value": lst[item]})
                except:
                    continue
            traceTables.append(" ")
    except:
        traceTables.clear

    v3_age_results, v3_plots, v3_diagnostics = _get_calculated_age_plot_diagnostics(
        v3_str, "age_input_v3")
    cl36_age_results, cl36_plots, cl36_diagnostics = _get_calculated_age_plot_diagnostics(
        cl36_str, "Cl36_input_v3")

    publications_match = SamplePublicationsMatch.get_publications_by_sample_ids(
        [sample_obj.id]
    )
    # MySQL doesn't support `DISTINCT ON` so uniquifying here using set
    publications = set([pm.publication for pm in publications_match])

    context = {
        "page_title": f"Comprehensive data dump for sample: {sample_obj.name}",
        "sample": sample_obj,
        "v3_str": v3_str,
        "v3_age_results": v3_age_results,
        "v3_plots": v3_plots,
        "v3_diagnostics": v3_diagnostics,
        "cl36_str": cl36_str,
        "cl36_age_results": cl36_age_results,
        "cl36_plots": cl36_plots,
        "cl36_diagnostics": cl36_diagnostics,
        "publications": publications,
        "table_name_to_proper_name": FieldProperName.get_proper_names(application_name),
        "n_tables": n_tables,
        "sampleTables": sampleTables,
        "albeTables": albeTables,
        "c14qTables": c14qTables,
        "he3qTables": he3qTables,
        "he3pxolTables": he3pxolTables,
        "ne21qTables": ne21qTables,
        "UThquartzTables": UThquartzTables,
        "cl36Tables": cl36Tables,
        "majorTables": majorTables,
        "traceTables": traceTables,
    } | application.get_application_ctx()

    template = loader.get_template("sample.html")
    return HttpResponse(template.render(context, request))
