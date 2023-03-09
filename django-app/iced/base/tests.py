from base.models import Application, Project
from django.test import TestCase


class ApplicationTestCase(TestCase):
    application_name = "Test Application"

    def setUp(self):
        Application.objects.create(name=self.application_name)

    def test_valid_application(self):
        """Application created and named properly"""
        test_application = Application.objects.get(name=self.application_name)
        self.assertEqual(test_application.name, self.application_name)


class ProjectTestCase(TestCase):
    project = "Test Project"
    people = "Test People"
    NSF_title = "Test NSF Title"
    year = 2021

    def setUp(self):
        Project.objects.create(
            project=self.project,
            people=self.people,
            NSF_title=self.NSF_title,
            year=self.year,
        )

    def test_valid_project(self):
        """Project created and named properly"""
        test_project = Project.objects.get(project=self.project)
        self.assertEqual(test_project.project, self.project)
