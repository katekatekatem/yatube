from http import HTTPStatus

from django.test import TestCase


class CoreTests(TestCase):

    def test_404_template(self):
        """Страница 404 отдаёт кастомный шаблон."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
