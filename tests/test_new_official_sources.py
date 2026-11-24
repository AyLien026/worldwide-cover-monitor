import unittest

from monitor import parse_official_news_links, parse_official_bulletins


class OfficialLinkSourcesTests(unittest.TestCase):
    def test_jersey_philately_links_only_and_no_duplicates(self):
        source = {
            "id": "jersey-stamps-news",
            "name": "Jersey Post – Philatelic Bureau news",
            "url": "https://jerseystamps.com/blogs/news",
            "url_pattern": r"^https://jerseystamps\.com/blogs/news/[^/?#]+",
            "title_pattern": r".+",
            "max_entries": 2,
            "category": "Philatelie",
        }
        html = """
          <a href="/collections/stamps">Shop</a>
          <a href="/blogs/news/2026-christmas">Christmas stamps 2026</a>
          <a href="/blogs/news/2026-christmas">Read More</a>
          <a href="/blogs/news/2026-airmail">Jersey Airmail History</a>
          <a href="https://external.example/blogs/news/untrusted">External</a>
        """
        items = parse_official_news_links(html, source)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "Christmas stamps 2026")
        self.assertEqual(items[1]["title"], "Jersey Airmail History")

    def test_isle_of_man_ignores_general_service_headlines(self):
        source = {
            "id": "isle-of-man-stamps-news",
            "name": "Isle of Man Post Office – Stamp news",
            "url": "https://www.iompost.com/news",
            "url_pattern": r"^https://www\.iompost\.com/news/[^?#]+",
            "title_pattern": r"stamp|stamps|philatel|collection|coins",
            "max_entries": 3
        }
        html = """
          <a href="/news/new-post-office-hours">Opening Hours</a>
          <a href="/news/island-stamp-issue">New island stamp issue</a>
        """
        self.assertEqual(len(parse_official_news_links(html, source)), 1)

    def test_faroese_pdf_bulletin(self):
        source = {
            "id": "faroes-posta-magazine",
            "name": "Faroe Islands – Posta Stamps philatelic magazine",
            "url": "https://en.stamps.fo/for-philatelists/philatelic-magazines/",
            "title_pattern": r"Posta Stamps \d{2}/20\d{2}",
            "pdf_only": True,
            "max_entries": 2
        }
        html = '<a href="/media/3151/faldari-2026-02_eng.pdf">Posta Stamps 02/2026</a>'
        items = parse_official_bulletins(html, source)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Posta Stamps 02/2026")
        self.assertTrue(items[0]["url"].endswith(".pdf"))


if __name__ == "__main__":
    unittest.main()
