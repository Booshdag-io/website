import base64
import unittest
from unittest.mock import Mock

from app.utils.github_requests import GithubClient


class ReadmeImageTests(unittest.TestCase):
    def extract(self, content, path="README.md"):
        client = GithubClient()
        response = Mock(status_code=200)
        response.json.return_value = {
            "path": path,
            "content": base64.b64encode(content.encode()).decode(),
        }
        client.session = Mock()
        client.session.get.return_value = response
        return client.get_repo_readme_image("owner", "project")

    def test_markdown_titles_and_angle_urls(self):
        for image in ['![Preview](assets/preview.png "Project preview")',
                      "![Preview](assets/preview.png 'Project preview')",
                      '![Preview](<assets/preview.png>)']:
            with self.subTest(image=image):
                self.assertEqual(self.extract(image),
                                 "https://raw.githubusercontent.com/owner/project/main/assets/preview.png")

    def test_first_image_across_html_and_markdown(self):
        self.assertEqual(self.extract('<img src="hero.png">\n![Badge](badge.png)'),
                         "https://raw.githubusercontent.com/owner/project/main/hero.png")

    def test_paths_are_resolved_relative_to_readme(self):
        for src, expected in [("images/preview.png", "docs/images/preview.png"),
                              ("../.github/preview.png", ".github/preview.png"),
                              ("/assets/preview.png", "assets/preview.png")]:
            with self.subTest(src=src):
                self.assertEqual(self.extract(f'![Preview]({src})', "docs/README.md"),
                                 f"https://raw.githubusercontent.com/owner/project/main/{expected}")

    def test_extensionless_github_attachment_precedes_badge(self):
        attachment = "https://github.com/user-attachments/assets/1234-5678"
        self.assertEqual(self.extract(f'![Preview]({attachment})\n![Badge](badge.svg)'), attachment)

    def test_empty_and_failed_readmes_fall_back(self):
        self.assertIsNone(self.extract("No images"))
        client = GithubClient()
        client.session = Mock()
        client.session.get.return_value = Mock(status_code=404)
        self.assertIsNone(client.get_repo_readme_image("owner", "project"))

    def test_protocol_relative_urls_and_unsafe_schemes(self):
        self.assertEqual(self.extract('![Preview](//raw.githubusercontent.com/a/b/main/image)'),
                         'https://raw.githubusercontent.com/a/b/main/image')
        self.assertIsNone(self.extract('![Bad](data:image/png;base64,abc)'))
