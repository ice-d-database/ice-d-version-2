from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from guardian.admin import GuardedModelAdmin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import (
    Al_stds,
    Application,
    Be10Al26Quartz,
    Be_stds,
    C14Quartz,
    Calculation,
    CalibrationData,
    CalibrationDataSample,
    Cl36,
    Continent,
    Core,
    CoreSample,
    CoresampleNuclideMatch,
    Document,
    FundingSource,
    GroupPermission,
    He3Pxol,
    He3Quartz,
    ImageFile,
    ImageFilesCores,
    ImageUrlPath,
    MajorElement,
    Ne21Quartz,
    Project,
    Publication,
    Region,
    Sample,
    SampleDocumentMatch,
    SamplePublicationsMatch,
    SampleUserData,
    Sector,
    Site,
    TraceElement,
    UserFieldsProperty,
    UserPermission,
    UThQuartz,
)


class ApplicationAdmin(ImportExportModelAdmin):
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        filter_horizontal = ('Site',)
        if request.user.is_superuser:
            queryset = Application.objects.all()
        else:
            groupList = list(request.user.groups.all().values_list("id", flat=True))
            groupAppList = list(
                GroupPermission.objects.filter(group_id__in=groupList).values_list(
                    "application_id", flat=True
                )
            )
            userAppList = list(
                UserPermission.objects.filter(user_id=request.user.id).values_list(
                    "application_id", flat=True
                )
            )
            fullList = groupAppList + userAppList
            queryset = Application.objects.filter(pk__in=fullList).order_by("id")

        return queryset


class UserPermissionResource(resources.ModelResource):
    class Meta:
        model = UserPermission


class GroupPermissionResource(resources.ModelResource):
    class Meta:
        model = GroupPermission


class UserPermissionAdmin(admin.ModelAdmin):
    resource_class = UserPermissionResource


class GroupPermissionAdmin(admin.ModelAdmin):
    resource_class = GroupPermissionResource


class SiteResource(resources.ModelResource):
    class Meta:
        model = Site

class PublicationResource(resources.ModelResource):
    class Meta:
        model = Publication


class CoreResource(resources.ModelResource):
    class Meta:
        model = Core


class CalculationResource(resources.ModelResource):
    class Meta:
        model = Calculation


class SampleResource(resources.ModelResource):
    class Meta:
        model = Sample


class CoreSampleResource(resources.ModelResource):
    class Meta:
        model = CoreSample


class SamplePublicationsMatchResource(resources.ModelResource):
    class Meta:
        model = SamplePublicationsMatch

class SamplePublicationsMatchAdmin(ImportExportModelAdmin):
    resource_class = SamplePublicationsMatchResource

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        if request.user.is_superuser:
            queryset = SamplePublicationsMatch.objects.all()
        else:
            groupList = list(request.user.groups.all().values_list("id", flat=True))
            groupAppList = list(
                GroupPermission.objects.filter(group_id__in=groupList).values_list(
                    "application_id", flat=True
                )
            )
            userAppList = list(
                UserPermission.objects.filter(user_id=request.user.id).values_list(
                    "application_id", flat=True
                )
            )
            fullList = groupAppList + userAppList
            # queryset = Site.objects.filter(application_id__in=fullList).order_by("id")
            queryset = Site.objects.filter(applications__id__in=fullList).order_by("id")

        return queryset

class CoresampleNuclideMatchResource(resources.ModelResource):
    class Meta:
        model = CoresampleNuclideMatch

class ApplicationInline(admin.TabularInline):
    model = Application.sites.through

class SiteAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = SiteResource
    inlines = [
        ApplicationInline
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        if request.user.is_superuser:
            queryset = Site.objects.all()
        else:
            groupList = list(request.user.groups.all().values_list("id", flat=True))
            groupAppList = list(
                GroupPermission.objects.filter(group_id__in=groupList).values_list(
                    "application_id", flat=True
                )
            )
            userAppList = list(
                UserPermission.objects.filter(user_id=request.user.id).values_list(
                    "application_id", flat=True
                )
            )
            fullList = groupAppList + userAppList
            # queryset = Site.objects.filter(application_id__in=fullList).order_by("id")
            queryset = Site.objects.filter(applications__id__in=fullList).order_by("id")

        return queryset


class ProjectAdmin(GuardedModelAdmin):
    pass


class CoreAdmin(ImportExportModelAdmin):
    resource_class = CoreResource

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        if request.user.is_superuser:
            queryset = Core.objects.all()
        else:
            groupList = list(request.user.groups.all().values_list("id", flat=True))
            groupAppList = list(
                GroupPermission.objects.filter(group_id__in=groupList).values_list(
                    "application_id", flat=True
                )
            )
            userAppList = list(
                UserPermission.objects.filter(user_id=request.user.id).values_list(
                    "application_id", flat=True
                )
            )
            fullList = groupAppList + userAppList
            siteList = list(
                Site.objects.filter(applications__id__in=fullList).values_list(
                    "id", flat=True
                )
            )
            queryset = Core.objects.filter(site_id__in=siteList).order_by("id")

        return queryset


class SampleAdmin(ImportExportModelAdmin):
    resource_class = SampleResource

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        if request.user.is_superuser:
            queryset = Sample.objects.all()
        else:
            groupList = list(request.user.groups.all().values_list("id", flat=True))
            groupAppList = list(
                GroupPermission.objects.filter(group_id__in=groupList).values_list(
                    "application_id", flat=True
                )
            )
            userAppList = list(
                UserPermission.objects.filter(user_id=request.user.id).values_list(
                    "application_id", flat=True
                )
            )
            fullList = groupAppList + userAppList
            siteList = list(
                Site.objects.filter(applications__id__in=fullList).values_list(
                    "id", flat=True
                )
            )
            queryset = Sample.objects.filter(site_id__in=siteList).order_by("id")

        return queryset


class CoreSampleAdmin(ImportExportModelAdmin):
    resource_class = CoreSampleResource

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        if request.user.is_superuser:
            queryset = CoreSample.objects.all()
        else:
            groupList = list(request.user.groups.all().values_list("id", flat=True))
            groupAppList = list(
                GroupPermission.objects.filter(group_id__in=groupList).values_list(
                    "application_id", flat=True
                )
            )
            userAppList = list(
                UserPermission.objects.filter(user_id=request.user.id).values_list(
                    "application_id", flat=True
                )
            )
            fullList = groupAppList + userAppList
            siteList = list(
                Site.objects.filter(applications__id__in=fullList).values_list(
                    "id", flat=True
                )
            )
            coreList = list(
                Core.objects.filter(site_id__in=siteList).values_list("id", flat=True)
            )
            queryset = CoreSample.objects.filter(core_id__in=coreList).order_by("id")

        return queryset


class CalculationAdmin(ImportExportModelAdmin):
    resource_class = CalculationResource
    list_display = ("name", "calculation_service_endpoint", "variable_json")

class PublicationAdmin(ImportExportModelAdmin):
    resource_class = PublicationResource

class CoreSampleNuclideMatchAdmin(ImportExportModelAdmin):
    resource_class = CoresampleNuclideMatchResource

# These are the nuclide match tables
class Be10Al26QuartzResource(resources.ModelResource):
    class Meta:
        model = Be10Al26Quartz

class Be10Al26QuartzAdmin(ImportExportModelAdmin):
    resource_class = Be10Al26QuartzResource

class C14QuartzResource(resources.ModelResource):
    class Meta:
        model = C14Quartz

class C14QuartzAdmin(ImportExportModelAdmin):
    resource_class = C14QuartzResource

class Cl36Resource(resources.ModelResource):
    class Meta:
        model = Cl36

class Cl36Admin(ImportExportModelAdmin):
    resource_class = Cl36Resource

class He3PxolResource(resources.ModelResource):
    class Meta:
        model = He3Pxol

class He3PxolAdmin(ImportExportModelAdmin):
    resource_class = He3PxolResource

class He3QuartzResource(resources.ModelResource):
    class Meta:
        model = He3Quartz

class He3QuartzAdmin(ImportExportModelAdmin):
    resource_class = He3QuartzResource

class MajorElementResource(resources.ModelResource):
    class Meta:
        model = MajorElement

class MajorElementAdmin(ImportExportModelAdmin):
    resource_class = MajorElementResource

class Ne21QuartzResource(resources.ModelResource):
    class Meta:
        model = Ne21Quartz

class Ne21QuartzAdmin(ImportExportModelAdmin):
    resource_class = Ne21QuartzResource

class TraceElementResource(resources.ModelResource):
    class Meta:
        model = TraceElement

class TraceElementAdmin(ImportExportModelAdmin):
    resource_class = TraceElementResource

class UThQuartzResource(resources.ModelResource):
    class Meta:
        model = UThQuartz

class UThQuartzAdmin(ImportExportModelAdmin):
    resource_class = UThQuartzResource

admin.site.register(Site, SiteAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(UserPermission, UserPermissionAdmin)
admin.site.register(GroupPermission, GroupPermissionAdmin)
admin.site.register(Core, CoreAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(CoreSample, CoreSampleAdmin)
admin.site.register(SamplePublicationsMatch, SamplePublicationsMatchAdmin)
admin.site.register(Calculation, CalculationAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(CoresampleNuclideMatch, CoreSampleNuclideMatchAdmin)
admin.site.register(Be10Al26Quartz, Be10Al26QuartzAdmin)
admin.site.register(C14Quartz, C14QuartzAdmin)
admin.site.register(Cl36, Cl36Admin)
admin.site.register(He3Pxol, He3PxolAdmin)
admin.site.register(He3Quartz, He3QuartzAdmin)
admin.site.register(MajorElement, MajorElementAdmin)
admin.site.register(Ne21Quartz, Ne21QuartzAdmin)
admin.site.register(TraceElement, TraceElementAdmin)
admin.site.register(UThQuartz, UThQuartzAdmin)
admin.site.register(Al_stds)
admin.site.register(Be_stds)
admin.site.register(CalibrationData)
admin.site.register(CalibrationDataSample)
admin.site.register(Continent)
admin.site.register(Document)
admin.site.register(FundingSource)
admin.site.register(ImageFile)
admin.site.register(ImageFilesCores)
admin.site.register(ImageUrlPath)
admin.site.register(Region)
admin.site.register(SampleDocumentMatch)
admin.site.register(SampleUserData)
admin.site.register(Sector)
admin.site.register(UserFieldsProperty)
