import re
from datetime import datetime
import bibtexparser

from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import connection, models
from django.db.models import Count, Max, Min, TextChoices
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey
from django.db.models.query import QuerySet
from django.utils import timezone

from .queries import (
    cl36_calculator_string_query,
    depth_nuclide_concentration_query,
    exposure_calculator_string_query,
    sample_nuclide_match_query,
)


def _format_nuclide_data(
    nuclide_matches: list[int], core_samples: bool = False
) -> dict:
    sample_data = {}
    if core_samples:
        for match in nuclide_matches:
            sample_data[match[0]] = {
                "sample_data": {
                    "name": match[1],
                    "top_depth_cm": match[2],
                    "bot_depth_cm": match[3],
                    "top_depth_gcm2": match[4],
                    "bot_depth_gcm2": match[5],
                    "measured_density": match[6],
                    "lithology": match[7],
                    "comments": match[8],
                },
                "Be10_Al26_quartz": {"N10_atoms_g": match[9], "N26_atoms_g": match[10]},
                "C14_quartz": {"N10_atoms_g": match[11]},
                "He3_quartz": {"N3c_atoms_g": match[12]},
                "He3_pxol": {"N3c_atoms_g": match[13]},
                "Ne21_quartz": {"N21xs_atoms_g": match[14]},
                "Cl36": {"id": match[15]},
            }
    else:
        for match in nuclide_matches:
            sample_data[match[0]] = {
                "sample_data": {
                    "name": match[1],
                    "latitude": match[2],
                    "longitude": match[3],
                    "elevation": match[4],
                    "lithology": match[5],
                    "what": match[6],
                    "site_short_name": match[7],
                },
                "Be10_Al26_quartz": {"N10_atoms_g": match[8], "N26_atoms_g": match[9]},
                "C14_quartz": {"N10_atoms_g": match[10]},
                "He3_quartz": {"N3c_atoms_g": match[11]},
                "He3_pxol": {"N3c_atoms_g": match[12]},
                "Ne21_quartz": {"N21xs_atoms_g": match[13]},
                "Cl36": {"id": match[14]},
            }

    return sample_data


class Region(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from="name", unique_with=["name"])

    def __str__(self):
        return f"{self.id} - ({self.name})"


class Sector(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from="name", unique_with=["name"])

    def __str__(self):
        return f"{self.id} - {self.name}"


class Continent(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from="name", unique_with=["name"])

    def __str__(self):
        return "{}".format(self.name)

    @staticmethod
    def get_continent_name_by_slug(slug: str):
        try:
            return Continent.objects.get(slug=slug).name
        except Continent.DoesNotExist:
            return None


class Application(models.Model):
    id = models.AutoField(primary_key=True)
    image = models.CharField(max_length=255, default="star_image.jpg")
    sites = models.ManyToManyField("Site", related_name="applications")
    description = models.TextField(null=True, blank=True)
    page_alert = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=255, unique=True)
    map_image = models.TextField(null=True, blank=True)
    interactive_map = models.BooleanField(default=False)
    page_alert = models.TextField(null=True, blank=True)
    credits = models.TextField(null=True, blank=True)
    NSF_funding = models.BooleanField(default=False)
    calibration_data_sets = models.BooleanField(default=False)
    link_color = models.CharField(max_length=8, default = "#888888")
    visited_color = models.CharField(max_length=8, default = "#666666")
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id} - {self.name}"

    @staticmethod
    def get_application_by_name(application_name: str) -> models.Model:
        try:
            return Application.objects.get(name__iexact=application_name)
        except Application.DoesNotExist:
            return None

    def get_application_ctx(self):
        return {
            "app_name": self.name,
            "header_img_path": f"img/{self.image}",
            "footer_credits": self.credits,
            "page_alert": self.page_alert,
            "interactive_map": self.interactive_map,
            "map_image": self.map_image + "?" if self.map_image else "",
            "NSF_funding": self.NSF_funding,
            "calibration_data_sets": self.calibration_data_sets,
            "link_color": self.link_color,
            "visited_color": self.visited_color
        }

    def get_sample_field_proper_names_dict(self, sample_type="base_coresample"):
        table_names = [
            "be10_al26_quartz",
            "c14_quartz",
            "he3_pxol",
            "he3_quartz",
            "ne21_quartz",
            "cl36",
            "u_th_quartz",
            "major_element",
            "trace_element",
            "base_sample",
            sample_type,
        ]
        proper_names_qs = FieldProperName.objects.filter(
            application=self, table_name__in=table_names
        )

        proper_names = {}

        for pn in proper_names_qs:
            if pn.table_name not in proper_names:
                proper_names[pn.table_name] = {}
            proper_names[pn.table_name][pn.field_name] = [
                pn.description,
                pn.format_string,
            ]

        return proper_names

    def get_sites(self):
        return self.sites.all()


class Site(models.Model):
    id = models.AutoField(primary_key=True)
    short_name = models.CharField(max_length=255, unique=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.TextField(null=True, blank=True)
    what = models.TextField(default='')
    project = models.ForeignKey(
        "Project", null=True, blank=True, on_delete=models.SET_NULL
    )
    dist_from_ice_margin_km = models.FloatField(null=True, blank=True)
    ht_above_ice_margin_m = models.FloatField(null=True, blank=True)
    implied_thickening_m = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    continent = models.ForeignKey(
        Continent, on_delete=models.SET_NULL, blank=True, null=True
    )
    range = models.TextField(null=True, blank=True)
    glacier = models.TextField(null=True, blank=True)
    site_min_truet = models.FloatField(null=True, blank=True)
    site_del_min_truet = models.FloatField(null=True, blank=True)
    site_max_truet = models.FloatField(null=True, blank=True)
    site_del_max_truet = models.FloatField(null=True, blank=True)
    site_truet = models.FloatField(null=True, blank=True)
    site_del_truet = models.FloatField(null=True, blank=True)
    annavg_SWE_cm = models.FloatField(null=True, blank=True)
    erosional_relief_cm = models.FloatField(null=True, blank=True)
    del_erosional_relief_cm = models.FloatField(null=True, blank=True)
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, blank=True, null=True)
    faultsystem = models.TextField(null=True, blank=True)
    fault_short_name = models.CharField(max_length=255, null=True, blank=True)
    older_than = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("short_name", "name", "region", "continent")

    def __str__(self):
        return f"{self.id} - ({self.short_name}) {self.name}"

    @property
    def samples_count(self) -> int:
        return Sample.objects.filter(site_id=self).count()

    @staticmethod
    def get_distinct_continents_by_application(application: Application) -> list:
        return (
            application.sites.all()
            .select_related("continent")
            .values_list("continent__slug", flat=True)
            .distinct()
        )

    @staticmethod
    def get_site_ids_by_application(application: Application) -> list:
        return application.sites.all().values_list("id", flat=True)

    class Meta:
        verbose_name_plural = "Sites"

    @staticmethod
    def get_sites_by_continent(application: Application, continent: Continent) -> list:
        return application.sites.all().filter(continent__slug=continent)


class Project(models.Model):
    MIN_YEAR = 1900
    MAX_YEAR = 2100
    MIN_YEAR_VALIDATOR = MinValueValidator(
        MIN_YEAR, f"You must select a year higher than {MIN_YEAR}"
    )
    MAX_YEAR_VALIDATOR = MaxValueValidator(
        MAX_YEAR, f"You must select a year before {MAX_YEAR}"
    )

    id = models.AutoField(primary_key=True)
    project = models.TextField(null=True, blank=True)
    people = models.TextField(null=True, blank=True)
    NSF_title = models.TextField(null=True, blank=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    year = models.IntegerField(
        null=True, blank=True, validators=[MIN_YEAR_VALIDATOR, MAX_YEAR_VALIDATOR]
    )
    funding_sources = models.ManyToManyField(
        "FundingSource", related_name="funding_sources"
    )
    samples = models.ManyToManyField("Sample", related_name="samples")
    
    cores = models.ManyToManyField("Core", related_name="cores")

    def __str__(self):
        return f"{self.id} - {self.project} ({self.NSF_title})"


class Sample(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    lat_DD = models.DecimalField(max_digits=13, decimal_places=10)
    lon_DD = models.DecimalField(max_digits=13, decimal_places=10)
    elv_m = models.FloatField()
    shielding = models.FloatField(null=True, blank=True)
    thick_cm = models.FloatField(null=True, blank=True)
    lithology = models.TextField(null=True, blank=True)
    site = models.ForeignKey(
        Site, on_delete=CASCADE, db_index=True, null=True, blank=True
    )
    density = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    what = models.TextField(default='')
    collected_by = models.TextField(null=True, blank=True)
    date_collected = models.DateField(null=True, blank=True)
    shielding_azimuths = models.TextField(null=True, blank=True)
    shielding_elevations = models.TextField(null=True, blank=True)
    local_ice_surface_m = models.FloatField(null=True, blank=True)
    USPRR_DB_id = models.TextField(null=True, blank=True)
    surface_strike = models.FloatField(null=True, blank=True)
    surface_dip = models.FloatField(null=True, blank=True)
    surfpt_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def get_by_sample_id(sampleID: int):
        try:
            return Sample.objects.get(pk=sampleID)
        except Sample.DoesNotExist:
            return None

    @staticmethod
    def get_sample_by_name(sampleName: str):
        try:
            return Sample.objects.get(name=sampleName)
        except Sample.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.id} - Sample: {self.name}"

    @staticmethod
    def get_samples_by_site(site_ids: list):
        return Sample.objects.filter(site__in=site_ids)

    @staticmethod
    def get_formatted_nuclide(sample_ids: list[int]) -> list[dict]:
        # Writing raw sql here gives us the results while remaining performant
        cursor = connection.cursor()
        sql = sample_nuclide_match_query(sample_ids)
        cursor.execute(sql)
        nuclide_matches = cursor.fetchall()
        data = _format_nuclide_data(nuclide_matches)

        return data

    @staticmethod
    def get_v3_age_calc_string(sample_ids, known_age=False):
        cursor = connection.cursor()
        sql = exposure_calculator_string_query(sample_ids, known_age=known_age)
        cursor.execute(sql)
        rows = cursor.fetchall()
        strings = filter(
            lambda x: x != "",
            [re.sub(" +;", ";", row[2].replace("\n ", "\n")).strip() for row in rows],
        )

        return "\n".join(strings)

    @staticmethod
    def get_cl36_age_calc_string(sample_ids):
        cursor = connection.cursor()
        sql = cl36_calculator_string_query(sample_ids)
        cursor.execute(sql)
        rows = cursor.fetchall()
        strings = filter(
            lambda x: x != "",
            [re.sub(" +;", ";", row[2].replace("\n ", "\n")).strip() for row in rows],
        )
        return "\n".join(strings)

    @property
    def field_photos(self):
        return ImageFile.objects.filter(
            sample_id=self.id, image_type="Field Image"
        ).select_related("image_url_path")

    @property
    def lab_photos(self):
        return ImageFile.objects.filter(
            sample_id=self.id, image_type="Lab Image"
        ).select_related("image_url_path")

    @property
    def documents(self):
        return (
            SampleDocumentMatch.objects.filter(sample_id=self.id)
            .select_related("document")
            .distinct()
        )

    @property
    def cl36_nuclides(self):
        return Cl36.objects.filter(sample_id=self.id)

    @property
    def major_elements(self):
        return MajorElement.objects.filter(sample_id=self.id)

    @property
    def trace_elements(self):
        return TraceElement.objects.filter(sample_id=self.id)

    def sample_user_data(self):
        return SampleUserData.objects.filter(sample_id=self.id)

    @staticmethod
    def exposure_calculator_string_query(sample_ids):
        cursor = connection.cursor()
        sql = exposure_calculator_string_query(sample_ids)
        cursor.execute(sql)
        rows = cursor.fetchall()
        strings = [
            row[2].strip().replace(" ;", ";").replace("\n ", "\n") for row in rows
        ]
        return "\n".join(strings)

    @staticmethod
    def cl36_calculator_string_query(sample_ids):
        cursor = connection.cursor()
        sql = cl36_calculator_string_query(sample_ids)
        cursor.execute(sql)
        rows = cursor.fetchall()
        strings = [
            row[2].strip().replace(" ;", ";").replace("\n ", "\n") for row in rows
        ]
        return "\n".join(strings)


class SampleUserData(models.Model):
    id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, null=True, blank=True, on_delete=models.CASCADE)
    field_name = models.TextField(null=True, blank=True)
    field_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        verbose_name_plural = "Sample User Data"


class Publication(models.Model):
    MIN_YEAR = MinValueValidator(1900, "You must select a year higher than 1900")
    MAX_YEAR = MaxValueValidator(2100, "You must select a year before current year")

    id = models.AutoField(primary_key=True)
    short_name = models.CharField(max_length=255)
    bibtex_record = models.TextField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True, validators=[MIN_YEAR, MAX_YEAR])
    doi = models.CharField(max_length=255, null=True, blank=True)

    # Publication.objects.filter(application)

    class Meta:
        unique_together = ("year", "short_name", "doi")

    def __str__(self):
        return f"{self.id} - ({self.short_name})"

    @staticmethod
    def get_publication_count_by_application(application: Application) -> int:
        site_list = application.get_sites()
        samples = Sample.get_samples_by_site(site_list)
        sample_ids = [sample.id for sample in samples]
        return SamplePublicationsMatch.objects.filter(sample_id__in=sample_ids,publication_id__isnull=False).count()

    @property
    def parsed_bibtex(self) -> dict:
        # fields = ["title", "author", "year", "journal"]
        # bibtex_records = {}
        # for field in fields:
        #    try:
        #        val = re.findall("%s={.*}" % field, self.bibtex_record)[0]
        #        valval = val[val.index("{") + 1: val.index("}")]
        #        bibtex_records[field] = valval.replace('\\','\\\\')
        #    except Exception as e:
        #        bibtex_records[field] = None
        #        pass

        parsed_bibtex = bibtexparser.loads(self.bibtex_record).entries
        if len(parsed_bibtex) > 0:
            bibtex_records = parsed_bibtex[0]
        else:
            bibtex_records = parsed_bibtex


        return bibtex_records

    def get_all_samples(self):
        match_records = SamplePublicationsMatch.objects.filter(publication_id=self.id)
        return [mr.sample for mr in match_records]

    def get_by_application(application):
        site_list = application.get_sites()
        samples = Sample.get_samples_by_site(site_list)
        sample_ids = [sample.id for sample in samples]

        cores_list = Core.get_cores_by_site(site_list)
        core_ids = [core.id for core in cores_list]
        core_samples = CoreSample.get_core_samples_by_core(core_ids)
        core_sample_ids = [cs.id for cs in core_samples]

        publications_by_sample = SamplePublicationsMatch.get_publications_by_sample_ids(sample_ids)
        publications_by_core_sample = SamplePublicationsMatch.get_publications_by_core_sample_ids(core_sample_ids)
        publications = publications_by_sample.union(publications_by_core_sample)
        return publications
    
    # Here insert a 'get_all_cores(self)' method using
    def get_all_cores(self):
        return Publication.objects.raw('select distinct base_core.* from base_core, base_coresample, base_samplepublicationsmatch where base_core.id = base_coresample.core_id and base_coresample.id = base_samplepublicationsmatch.core_sample_id and base_samplepublicationsmatch.publication_id = %s',[self.id])


class Document(models.Model):
    id = models.AutoField(primary_key=True)
    file_name = models.TextField(null=True, blank=True)
    url_path = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    publications = models.ManyToManyField("Publication")

    def __str__(self):
        return f"{self.id} - ({self.file_name})"


class FundingSource(models.Model):
    id = models.AutoField(primary_key=True)
    funding_source_name = models.TextField(null=True, blank=True)
    funding_source_id = models.CharField(max_length=255, null=True, blank=True)
    people_involved = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.people_involved})"


class ImageUrlPath(models.Model):
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=255)
    thumb_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.thumb_path})"


class ImageFile(models.Model):
    class ImageType(models.TextChoices):
        FIELD_IMAGE = 'Field Image'
        LAB_IMAGE = 'Lab Image'

    id = models.AutoField(primary_key=True)
    caption = models.TextField(null=True, blank=True)
    photo_file_id = models.TextField(null=True, blank=True)
    photographer = models.TextField(null=True, blank=True)
    photo_filename = models.TextField(null=True, blank=True)
    display_photo_filename = models.TextField(null=True, blank=True)
    image_type = models.CharField(max_length=255, choices=ImageType.choices)
    sample = models.ForeignKey(Sample, on_delete=CASCADE, null=True)
    image_url_path = models.ForeignKey(ImageUrlPath, on_delete=CASCADE, null=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"


class Core(models.Model):
    name = models.CharField(max_length=50, db_index=True, unique=True)
    description = models.TextField()
    lat_DD = models.DecimalField(max_digits=13, decimal_places=10)
    lon_DD = models.DecimalField(max_digits=13, decimal_places=10)
    elv_m = models.FloatField()
    shielding = models.FloatField(null=True, blank=True)
    # was locality_short_name, but changed to site_id
    site = models.ForeignKey(
        Site, on_delete=CASCADE, db_index=True, related_name="cores"
    )
    what = models.TextField(null=True, blank=True)
    shielding_azimuths = models.TextField(null=True, blank=True)
    shielding_elevations = models.TextField(null=True, blank=True)
    strike = models.FloatField(null=True, blank=True)
    dip = models.FloatField(null=True, blank=True)
    date_collected = models.DateField(null=True, blank=True)
    collected_by = models.TextField(null=True, blank=True)
    local_ice_surface_m = models.FloatField(null=True, blank=True)
    ice_cover_thickness_gcm2 = models.FloatField(null=True, blank=True)
    ice_cover_thickness_m = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    surfpt_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.id} - Core: {self.name}"

    @staticmethod
    def get_core_by_name(core_name: str) -> models.Model:
        try:
            return Core.objects.get(name__iexact=core_name)
        except Core.DoesNotExist:
            return None

    @staticmethod
    def get_core_count_by_sites(site_ids: list) -> int:
        return Core.objects.values_list("id").filter(site__in=site_ids).count()

    def get_all_core_samples(self) -> QuerySet:
        return CoreSample.objects.filter(core=self.id)

    def get_depth_nuclide_concentration(self) -> str:
        cursor = connection.cursor()
        sql = depth_nuclide_concentration_query(self.id)
        cursor.execute(sql)
        depth_nuclide = cursor.fetchall()
        return depth_nuclide[0][0]

    @staticmethod
    def get_cores_by_site(site_id:list):
        return Core.objects.filter(site_id__in=site_id)


class CoreSample(models.Model):
    core = models.ForeignKey(
        Core,
        on_delete=CASCADE,
        db_index=True,
    )
    name = models.CharField(max_length=255, db_index=True, unique=True)
    top_depth_cm = models.FloatField(null=True, blank=True)
    bot_depth_cm = models.FloatField(null=True, blank=True)
    top_depth_gcm2 = models.FloatField(null=True, blank=True)
    bot_depth_gcm2 = models.FloatField(null=True, blank=True)
    measured_density = models.FloatField(null=True, blank=True)
    lithology = models.TextField(null=True, blank=True)
    sediment_conc_wtwt = models.FloatField(null=True, blank=True)
    quartz_extracted_g = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - Core Sample: {self.name}"

    @staticmethod
    def get_core_sample_by_name(sampleName: str):
        return CoreSample.objects.select_related("core").get(name=sampleName)

    @staticmethod
    def get_formatted_nuclide(core_sample_ids: list[int]) -> list[dict]:
        # Writing raw sql here gives us the results while remaining performant
        cursor = connection.cursor()
        sql = sample_nuclide_match_query(core_sample_ids, core_samples=True)
        cursor.execute(sql)
        nuclide_matches = cursor.fetchall()
        data = _format_nuclide_data(nuclide_matches, core_samples=True)

        return data

    @property
    def get_core_photos(self):
        # This gets a list of core image files. The query matches the top and bottom depths shown in an
        # image to the top and bottom depths of the core sample.
        return ImageFilesCores.objects.raw('select * from base_imagefilescores where core_id = %s and ((top_depth_cm >= %s and top_depth_cm < %s) or (bot_depth_cm >= %s and bot_depth_cm < %s) or (top_depth_cm <= %s and bot_depth_cm >= %s)) order by top_depth_cm',[self.core.id, self.top_depth_cm, self.bot_depth_cm, self.top_depth_cm, self.bot_depth_cm, self.top_depth_cm, self.bot_depth_cm])

    @staticmethod
    def get_core_samples_by_core(cores_list):
        return CoreSample.objects.filter(core_id__in=cores_list)

class SamplePublicationsMatch(models.Model):
    id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, on_delete=CASCADE, null=True, blank=True)
    publication = models.ForeignKey(Publication, on_delete=CASCADE)
    core_sample = models.ForeignKey(
        CoreSample, on_delete=CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.id} - ({self.sample}) - ({self.publication})"

    class Meta:
        verbose_name_plural = "Sample Publication Matches"

    @staticmethod
    def get_publications_by_core_sample_ids(core_sample_ids):
        return SamplePublicationsMatch.objects.select_related("publication").filter(
            core_sample__in=core_sample_ids
        )

    @staticmethod
    def get_publications_by_sample_ids(sample_ids):
        return SamplePublicationsMatch.objects.select_related("publication").filter(
            sample__in=sample_ids
        )

class SampleDocumentMatch(models.Model):
    id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, on_delete=CASCADE, null=True)
    coresample = models.ForeignKey(CoreSample, on_delete=CASCADE, null=True)
    document = models.ForeignKey(Document, on_delete=CASCADE)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        verbose_name_plural = "Sample Document Matches"


class Calculation(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    calculation_service_endpoint = models.CharField(max_length=255)
    variable_json = models.TextField(null=True, blank=True)

    @staticmethod
    def get_calculation_by_name(calculationName: str):
        try:
            return Calculation.objects.get(name=calculationName)
        except Calculation.DoesNotExist:
            return None


# Sample Data Inputs


class He3Pxol(models.Model):
    sample = models.ForeignKey(Sample, null=True, blank=True, on_delete=models.CASCADE)
    aliquot = models.TextField(null=True, blank=True)
    mineral = models.TextField(null=True, blank=True)
    aliquot_wt_g = models.FloatField(null=True, blank=True)
    analysis_date = models.DateField(null=True, blank=True)
    N3c_atoms_g = models.FloatField(null=True, blank=True)
    delN3c_atoms_g = models.FloatField(null=True, blank=True)
    system = models.TextField(null=True, blank=True)
    standard = models.TextField(null=True, blank=True)
    std_N3_atoms_g = models.FloatField(null=True, blank=True)
    std_delN3_atoms_g = models.FloatField(null=True, blank=True)
    analyst = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    N4_atoms_g = models.FloatField(null=True, blank=True)
    delN4_atoms_g = models.FloatField(null=True, blank=True)
    N3inh_atoms_g = models.FloatField(null=True, blank=True)
    delN3inh_atoms_g = models.FloatField(null=True, blank=True)
    min_gs_um_initial = models.FloatField(null=True, blank=True)
    max_gs_um_initial = models.FloatField(null=True, blank=True)
    min_gs_um_after_crush = models.FloatField(null=True, blank=True)
    max_gs_um_after_crush = models.FloatField(null=True, blank=True)
    N3b_subtracted_atoms = models.FloatField(null=True, blank=True)
    N3total_atoms_g = models.FloatField(null=True, blank=True)
    delN3total_atoms_g = models.FloatField(null=True, blank=True)
    closure_age_Ma = models.FloatField(null=True, blank=True)
    delclosure_age_Ma = models.FloatField(null=True, blank=True)
    N3b_subtracted_atoms = models.FloatField(null=True, blank=True)
    delN3b_subtracted_atoms = models.FloatField(null=True, blank=True)
    analysis_method = models.FloatField(null=True, blank=True)
    r_factor = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_he3_pxol"
        verbose_name_plural = "He3 PXOL"

    @staticmethod
    def get_by_sample_id(sampleID: int):
        try:
            return He3Pxol.objects.get(sample_id=sampleID)
        except He3Pxol.DoesNotExist:
            return None

    @staticmethod
    def get_list_by_sample_id(sampleID: int):
        return list(He3Pxol.objects.filter(sample_id=sampleID))


class UThQuartz(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, blank=True, null=True)
    aliquot = models.TextField(null=True, blank=True)
    aliquot_wt_g = models.FloatField(null=True, blank=True)
    U_ppm = models.FloatField(null=True, blank=True)
    Th_ppm = models.FloatField(null=True, blank=True)
    lab = models.TextField(null=True, blank=True)
    analysis_type = models.TextField(null=True, blank=True)
    analysis_date = models.DateField(null=True, blank=True)
    analyst = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_u_th_quartz"
        verbose_name_plural = "U Th Quartz"


class TraceElement(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, blank=True, null=True)
    aliquot = models.TextField(null=True, blank=True)
    Li_ppm = models.FloatField(null=True, blank=True)
    B_ppm = models.FloatField(null=True, blank=True)
    Cl_ppm = models.FloatField(null=True, blank=True)
    Cr_ppm = models.FloatField(null=True, blank=True)
    Co_ppm = models.FloatField(null=True, blank=True)
    Sm_ppm = models.FloatField(null=True, blank=True)
    Gd_ppm = models.FloatField(null=True, blank=True)
    Th_ppm = models.FloatField(null=True, blank=True)
    delTh_ppm = models.FloatField(null=True, blank=True)
    U_ppm = models.FloatField(null=True, blank=True)
    delU_ppm = models.FloatField(null=True, blank=True)
    analysis_type = models.TextField(null=True, blank=True)
    lab = models.TextField(null=True, blank=True)
    lab_code = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_trace_element"


class Ne21Quartz(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, blank=True, null=True)
    aliquot = models.TextField(null=True, blank=True)
    aliquot_wt_g = models.FloatField(null=True, blank=True)
    analysis_date = models.DateField(null=True, blank=True)
    N21xs_atoms_g = models.FloatField(null=True, blank=True)
    delN21xs_atoms_g = models.FloatField(null=True, blank=True)
    N21inh_est_atoms_g = models.FloatField(null=True, blank=True)
    delN21inh_est_atoms_g = models.FloatField(null=True, blank=True)
    system = models.TextField(null=True, blank=True)
    standard = models.TextField(null=True, blank=True)
    std_N21c_atoms_g = models.IntegerField(null=True, blank=True)
    std_delN21c_atoms_g = models.IntegerField(null=True, blank=True)
    analyst = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_ne21_quartz"
        verbose_name_plural = "Ne21 Quartz"

    @staticmethod
    def get_by_sample_id(sampleID: int):
        try:
            return Ne21Quartz.objects.get(sample_id=sampleID)
        except Ne21Quartz.DoesNotExist:
            return None

    @staticmethod
    def get_list_by_sample_id(sampleID: int):
        return list(Ne21Quartz.objects.filter(sample_id=sampleID))

    def get_n21_table_data(core: Core):
        """Get data needed to create nuclide tables for given core"""
        ne21_table_data = (
            CoresampleNuclideMatch.objects.values(
                "Ne21_quartz__delN21xs_atoms_g", "Ne21_quartz__N21xs_atoms_g"
            )
            .filter(coresample_id__core_id=core.id, Ne21_quartz__N21xs_atoms_g__gt=0)
            .annotate(
                total_ne21_qtz=Count("Ne21_quartz_id"),
                min_top_depth_cm=Min("coresamples__top_depth_cm"),
                max_bot_depth_cm=Max("coresamples__bot_depth_cm"),
                min_top_depth_gcm2=Min("coresamples__top_depth_gcm2"),
                max_bot_depth_gcm2=Max("coresamples__bot_depth_gcm2"),
            )
            .order_by("Ne21_quartz_id")
        )

        headers = [
            "top depth cm",
            "bot depth cm",
            "top mass depth gcm2",
            "bot mass depth gcm2",
            "N21",
            "delN21",
            "num samples combined",
        ]

        rows = []
        for row in ne21_table_data:
            row_data = [
                row["min_top_depth_cm"],
                row["max_bot_depth_cm"],
                row["min_top_depth_gcm2"],
                row["max_bot_depth_gcm2"],
                row["Ne21_quartz__N21xs_atoms_g"],
                row["Ne21_quartz__delN21xs_atoms_g"],
                row["total_ne21_qtz"],
            ]
            rows.append(row_data)

        return headers, rows


class Cl36(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, blank=True, null=True)
    aliquot = models.TextField(null=True, blank=True)
    aliquot_wt_g = models.FloatField(null=True, blank=True)
    mineral = models.TextField(null=True, blank=True)
    chem_lab = models.TextField(null=True, blank=True)
    chem_lab_date = models.DateField(null=True, blank=True)
    chem_lab_id = models.TextField(null=True, blank=True)
    analyst = models.TextField(null=True, blank=True)
    Cl_AMS_lab = models.TextField(null=True, blank=True)
    Cl_AMS_date = models.DateField(null=True, blank=True)
    Cl_AMS_lab_id = models.TextField(null=True, blank=True)
    N36_atoms_g = models.FloatField(null=True, blank=True)
    delN36_atoms_g = models.FloatField(null=True, blank=True)
    target_Cl_ppm = models.FloatField(null=True, blank=True)
    deltarget_Cl_ppm = models.FloatField(null=True, blank=True)
    Cl_covariance = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    formation_age_Ma = models.FloatField(null=True, blank=True)
    delformation_age_Ma = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_cl36"
        verbose_name_plural = "CL36"


class Be10Al26Quartz(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, blank=True, null=True)
    aliquot = models.TextField(null=True, blank=True)
    aliquot_wt_g = models.FloatField(null=True, blank=True)
    chem_lab = models.TextField(null=True, blank=True)
    chem_lab_date = models.DateField(null=True, blank=True)
    chem_lab_id = models.TextField(null=True, blank=True)
    analyst = models.TextField(null=True, blank=True)
    Be_AMS_lab = models.TextField(null=True, blank=True)
    Be_AMS_date = models.DateField(null=True, blank=True)
    Be_AMS_lab_id = models.TextField(null=True, blank=True)
    N10_atoms_g = models.FloatField(null=True, blank=True)
    delN10_atoms_g = models.FloatField(null=True, blank=True)
    N10b_subtracted_atoms = models.FloatField(null=True, blank=True)
    delN10b_subtracted_atoms = models.FloatField(null=True, blank=True)
    Be10_std = models.TextField(null=True, blank=True)
    qtz_Al_ppm = models.FloatField(null=True, blank=True)
    delqtz_Al_ppm = models.FloatField(null=True, blank=True)
    Al_AMS_lab = models.TextField(null=True, blank=True)
    Al_AMS_date = models.DateField(null=True, blank=True)
    Al_AMS_lab_id = models.TextField(null=True, blank=True)
    N26_atoms_g = models.FloatField(null=True, blank=True)
    delN26_atoms_g = models.FloatField(null=True, blank=True)
    N26b_subtracted_atoms = models.FloatField(null=True, blank=True)
    delN26b_subtracted_atoms = models.FloatField(null=True, blank=True)
    Al26_std = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_be10_al26_quartz"
        verbose_name = "Be10 Al26 Quartz"
        verbose_name_plural = "Be10 Al26 Quartz"

    @staticmethod
    def get_by_sample_id(sampleID: int):
        try:
            return Be10Al26Quartz.objects.get(sample_id=sampleID)
        except Be10Al26Quartz.DoesNotExist:
            return None

    @staticmethod
    def get_list_by_sample_id(sampleID: int):
        return list(Be10Al26Quartz.objects.filter(sample_id=sampleID))

    @staticmethod
    def get_n10_table_data(core: Core):
        """Get data needed to create nuclide tables for given core"""
        be10_table_data = (
            CoresampleNuclideMatch.objects.values(
                "Be10_Al26_quartz__delN10_atoms_g", "Be10_Al26_quartz__N10_atoms_g"
            )
            .filter(
                coresample_id__core_id=core.id,
                Be10_Al26_quartz__N10_atoms_g__gt=0,
            )
            .annotate(
                total_be10_qtz=Count("Be10_Al26_quartz_id"),
                min_top_depth_cm=Min("coresamples__top_depth_cm"),
                max_bot_depth_cm=Max("coresamples__bot_depth_cm"),
                min_top_depth_gcm2=Min("coresamples__top_depth_gcm2"),
                max_bot_depth_gcm2=Max("coresamples__bot_depth_gcm2"),
            )
            .order_by("Be10_Al26_quartz_id")
        )

        headers = [
            "top depth cm",
            "bot depth cm",
            "top mass depth gcm2",
            "bot mass depth gcm2",
            "N10",
            "delN10",
            "num samples combined",
        ]

        rows = []
        for row in be10_table_data:
            row_data = [
                row["min_top_depth_cm"],
                row["max_bot_depth_cm"],
                row["min_top_depth_gcm2"],
                row["max_bot_depth_gcm2"],
                row["Be10_Al26_quartz__N10_atoms_g"],
                row["Be10_Al26_quartz__delN10_atoms_g"],
                row["total_be10_qtz"],
            ]
            rows.append(row_data)

        return headers, rows

    @staticmethod
    def get_n26_table_data(core: Core):
        """Get data needed to create nuclide tables for given core"""
        be10_table_data = (
            CoresampleNuclideMatch.objects.values(
                "Be10_Al26_quartz__delN26_atoms_g", "Be10_Al26_quartz__N26_atoms_g"
            )
            .filter(
                coresample_id__core_id=core.id,
                Be10_Al26_quartz__N26_atoms_g__gt=0,
            )
            .annotate(
                total_al26_qtz=Count("Be10_Al26_quartz_id"),
                min_top_depth_cm=Min("coresamples__top_depth_cm"),
                max_bot_depth_cm=Max("coresamples__bot_depth_cm"),
                min_top_depth_gcm2=Min("coresamples__top_depth_gcm2"),
                max_bot_depth_gcm2=Max("coresamples__bot_depth_gcm2"),
            )
            .order_by("Be10_Al26_quartz_id")
        )

        headers = [
            "top depth cm",
            "bot depth cm",
            "top mass depth gcm2",
            "bot mass depth gcm2",
            "N26",
            "delN26",
            "num samples combined",
        ]

        rows = []
        for row in be10_table_data:
            row_data = [
                row["min_top_depth_cm"],
                row["max_bot_depth_cm"],
                row["min_top_depth_gcm2"],
                row["max_bot_depth_gcm2"],
                row["Be10_Al26_quartz__N26_atoms_g"],
                row["Be10_Al26_quartz__delN26_atoms_g"],
                row["total_al26_qtz"],
            ]
            rows.append(row_data)

        return headers, rows


class C14Quartz(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, blank=True, null=True)
    aliquot = models.TextField(null=True, blank=True)
    aliquot_wt_g = models.FloatField(null=True, blank=True)
    extraction_date = models.DateField(null=True, blank=True)
    analysis_date = models.DateField(null=True, blank=True)
    N14_atoms_g = models.FloatField(null=True, blank=True)
    delN14_atoms_g = models.FloatField(null=True, blank=True)
    extraction_lab = models.TextField(null=True, blank=True)
    AMS_lab = models.TextField(null=True, blank=True)
    extraction_lab_id = models.TextField(null=True, blank=True)
    AMS_lab_id = models.TextField(null=True, blank=True)
    AMS_date = models.DateField(null=True, blank=True)
    analyst = models.TextField(null=True, blank=True)
    N14b_subtracted_atoms = models.FloatField(null=True, blank=True)
    delN14b_subtracted_atoms = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    standard = models.TextField(null=True, blank=True)
    std_N14c_atoms_g = models.FloatField(null=True, blank=True)
    std_delN14c_atoms_g = models.FloatField(null=True, blank=True)
    C_mass_ug = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_c14_quartz"
        verbose_name_plural = "C14 Quartz"

    @staticmethod
    def get_by_sample_id(sampleID: int):
        try:
            return C14Quartz.objects.get(sample_id=sampleID)
        except C14Quartz.DoesNotExist:
            return None

    @staticmethod
    def get_list_by_sample_id(sampleID: int):
        return list(C14Quartz.objects.filter(sample_id=sampleID))


class MajorElement(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, blank=True, null=True)
    aliquot = models.TextField(null=True, blank=True)
    what = models.TextField(null=True, blank=True)
    LOI_pct_wt = models.FloatField(null=True, blank=True)
    H_pct_wt = models.FloatField(null=True, blank=True)
    C_pct_wt = models.FloatField(null=True, blank=True)
    O_pct_wt = models.FloatField(null=True, blank=True)
    Na_pct_wt = models.FloatField(null=True, blank=True)
    Mg_pct_wt = models.FloatField(null=True, blank=True)
    Al_pct_wt = models.FloatField(null=True, blank=True)
    Si_pct_wt = models.FloatField(null=True, blank=True)
    P_pct_wt = models.FloatField(null=True, blank=True)
    S_pct_wt = models.FloatField(null=True, blank=True)
    K_pct_wt = models.FloatField(null=True, blank=True)
    delK_pct_wt = models.FloatField(null=True, blank=True)
    Ca_pct_wt = models.FloatField(null=True, blank=True)
    delCa_pct_wt = models.FloatField(null=True, blank=True)
    Ti_pct_wt = models.FloatField(null=True, blank=True)
    delTi_pct_wt = models.FloatField(null=True, blank=True)
    Mn_pct_wt = models.FloatField(null=True, blank=True)
    Fe_pct_wt = models.FloatField(null=True, blank=True)
    delFe_pct_wt = models.FloatField(null=True, blank=True)
    analysis_type = models.TextField(null=True, blank=True)
    lab = models.TextField(null=True, blank=True)
    lab_code = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_major_element"


class He3Quartz(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, blank=True, null=True)
    aliquot = models.TextField(null=True, blank=True)
    aliquot_wt_g = models.FloatField(null=True, blank=True)
    analysis_date = models.DateField(null=True, blank=True)
    N3c_atoms_g = models.FloatField(null=True, blank=True)
    delN3c_atoms_g = models.FloatField(null=True, blank=True)
    system = models.TextField(null=True, blank=True)
    standard = models.TextField(null=True, blank=True)
    std_N3_atoms_g = models.FloatField(null=True, blank=True)
    std_delN3_atoms_g = models.FloatField(null=True, blank=True)
    analyst = models.TextField(null=True, blank=True)
    min_gs_um = models.FloatField(null=True, blank=True)
    max_gs_um = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        db_table = "_he3_quartz"
        verbose_name_plural = "He3 Quartz"

    @staticmethod
    def get_by_sample_id(sampleID: int):
        try:
            return He3Quartz.objects.get(sample_id=sampleID)
        except He3Quartz.DoesNotExist:
            return None

    @staticmethod
    def get_list_by_sample_id(sampleID: int):
        return list(He3Quartz.objects.filter(sample_id=sampleID))


class CoresampleNuclideMatch(models.Model):
    coresample = models.ForeignKey(
        CoreSample,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    be10_al26_quartz = models.ForeignKey(
        Be10Al26Quartz,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    c14_quartz = models.ForeignKey(
        C14Quartz,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    cl36 = models.ForeignKey(
        Cl36,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    he3_pxol = models.ForeignKey(
        He3Pxol,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    he3_quartz = models.ForeignKey(
        He3Quartz,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    ne21_quartz = models.ForeignKey(
        Ne21Quartz,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    major_element = models.ForeignKey(
        MajorElement,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    trace_element = models.ForeignKey(
        TraceElement,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    u_th_quartz = models.ForeignKey(
        UThQuartz,
        on_delete=CASCADE,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Coresample Nuclide Match"

    class Meta:
        verbose_name_plural = "Core Sample Nuclide Matches"

    @staticmethod
    def get_nuclide_match_data(coresample):
        results = CoresampleNuclideMatch.objects.select_related(
            "coresample",
            "be10_al26_quartz",
            "c14_quartz",
            "cl36",
            "he3_pxol",
            "he3_quartz",
            "ne21_quartz",
            "major_element",
            "trace_element",
            "u_th_quartz",
        ).filter(coresample=coresample)
        return results


class UserPermission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, null=True)
    application = models.ForeignKey(Application, on_delete=CASCADE, null=True)

    def __str__(self):
        return f"User: {self.user} - Application: {self.application.name}"

    class Meta:
        verbose_name_plural = "User Permissions"


class GroupPermission(models.Model):
    group = models.ForeignKey(Group, on_delete=CASCADE, null=True)
    application = models.ForeignKey(Application, on_delete=CASCADE, null=True)

    def __str__(self):
        return f"Group: {self.group} - Application: {self.application.name}"

    class Meta:
        verbose_name_plural = "Group Permissions"


class UserFieldsProperty(models.Model):
    field_name = models.TextField(null=True, blank=True)
    owner = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    units = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.field_name} - {self.owner}"

    class Meta:
        verbose_name_plural = "User Fields Properties"


class FieldProperName(models.Model):
    table_name = models.CharField(max_length=255, null=True, blank=True)
    field_name = models.CharField(max_length=255, null=True, blank=True)
    format_string = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    application = models.ForeignKey(Application, on_delete=CASCADE)

    class Meta:
        unique_together = ("table_name", "field_name", "application")

    @staticmethod
    def get_proper_names(application_id: str) -> dict:
        table_name_to_proper_name = {}
        for table_name in (
            "sample",
            "Be10_Al26_quartz",
            "C14_quartz",
            "He3_pxol",
            "He3_quartz",
            "Ne21_quartz",
            "U_Th_quartz",
            "Cl36",
            "major_element",
            "trace_element",
            "coresample",
        ):
            proper_names = FieldProperName.objects.filter(table_name=table_name)
            table_name_to_proper_name[table_name] = proper_names
        return table_name_to_proper_name


class Updates(models.Model):
    when = models.DateTimeField(null=True, blank=True)
    table_affected = models.CharField(max_length=255, null=True, blank=True)
    sample = ForeignKey(Sample, on_delete=CASCADE, null=True, blank=True)
    sample_name = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
    )
    complete = models.BooleanField(null=False, default=False)
    user = CharField(max_length=255, null=True, blank=True)
    user2 = CharField(max_length=255, null=True, blank=True)


class CalculatedAge(models.Model):
    sample = ForeignKey(Sample, on_delete=CASCADE, null=True, blank=True)
    # this column may be redundant after creating the above foreign key
    when_updated = models.DateTimeField(null=True, blank=True, auto_now=True)
    nuclide = models.TextField(null=True, blank=True)
    t_St = models.FloatField(null=True, blank=True)
    dtint_St = models.FloatField(null=True, blank=True)
    dtext_St = models.FloatField(null=True, blank=True)
    t_Lm = models.FloatField(null=True, blank=True)
    dtint_Lm = models.FloatField(null=True, blank=True)
    dtext_Lm = models.FloatField(null=True, blank=True)
    t_LSDn = models.FloatField(null=True, blank=True)
    dtint_LSDn = models.FloatField(null=True, blank=True)
    dtext_LSDn = models.FloatField(null=True, blank=True)
    Nnorm_St = models.FloatField(null=True, blank=True)
    dNnorm_St = models.FloatField(null=True, blank=True)
    dNnorm_ext_St = models.FloatField(null=True, blank=True)
    Nnorm_Lm = models.FloatField(null=True, blank=True)
    dNnorm_Lm = models.FloatField(null=True, blank=True)
    dNnorm_ext_Lm = models.FloatField(null=True, blank=True)
    Nnorm_LSDn = models.FloatField(null=True, blank=True)
    dNnorm_LSDn = models.FloatField(null=True, blank=True)
    dNnorm_ext_LSDn = models.FloatField(null=True, blank=True)


class ImageFilesCores(models.Model):
    id = models.AutoField(primary_key=True)
    core = models.ForeignKey(Core, null=True, blank=True, on_delete=CASCADE)
    caption = models.TextField(null=True, blank=True)
    photographer = models.TextField(null=True, blank=True)
    photo_filename = models.TextField(null=True, blank=True)
    display_photo_filename = models.TextField(null=True, blank=True)
    top_depth_cm = models.FloatField(null=True, blank=True)
    bot_depth_cm = models.FloatField(null=True, blank=True)
    image_url_path = models.ForeignKey(ImageUrlPath, on_delete=CASCADE, null=True)

    def __str__(self):
        return f"{self.id} - ({self.core})"

    class Meta:
        verbose_name_plural = "Image File Cores"


class DataFileMigration(models.Model):
    name = models.CharField(max_length=255, null=False)
    applied = models.DateTimeField(null=False)


class Job(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True, unique=True)
    last_run = models.DateTimeField(null=True, blank=True)
    last_id = models.IntegerField(null=True, blank=True)

    def get(jobName: str):
        obj, created = Job.objects.update_or_create(
            name=jobName,
        )
        return obj

    def update_timestamp(jobName: str, timestamp: datetime = None):
        try:
            obj = Job.objects.get(name=jobName)
        except Job.DoesNotExist:
            return None
        if not datetime:
            timestamp = timezone.now()
        obj.last_run = timestamp
        obj.save()
        return obj

    def update_last_id(jobName: str, id: int):
        try:
            obj = Job.objects.get(name=jobName)
        except Job.DoesNotExist:
            return None
        obj.last_id = id
        obj.save()
        return obj


class Be_stds(models.Model):
    std_name = models.CharField(max_length=255, null=True, blank=True)
    cf = models.FloatField(null=True, blank=True)
    sample = models.ForeignKey(Sample, on_delete=CASCADE, null=True, blank=True)

    def __str__(self):
        return "{}".format(self.sample)

    class Meta:
        verbose_name_plural = "Be Stds"


class Al_stds(models.Model):
    std_name = models.CharField(max_length=255, null=True, blank=True)
    cf = models.FloatField(null=True, blank=True)
    sample = models.ForeignKey(Sample, on_delete=CASCADE, null=True, blank=True)

    def __str__(self):
        return "{}".format(self.sample)

    class Meta:
        verbose_name_plural = "Al Stds"


class CalibrationData(models.Model):
    name = models.CharField(max_length=255)
    publication = models.ForeignKey(Publication, on_delete=CASCADE)
    nuclide = models.CharField(max_length=50)
    description = models.TextField()
    samples = models.ManyToManyField(
        "Sample", related_name="cd_samples", through="CalibrationDataSample"
    )

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        verbose_name_plural = "Calibration Data"


class CalibrationDataSample(models.Model):
    sample = models.ForeignKey("Sample", on_delete=CASCADE)
    calibration_data = models.ForeignKey("CalibrationData", on_delete=CASCADE)
    aliquot = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.id} - ({self.sample})"

    class Meta:
        unique_together = ("calibration_data", "sample", "aliquot")
