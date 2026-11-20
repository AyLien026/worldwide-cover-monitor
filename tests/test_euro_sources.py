"""Regression tests for official euro-area bulletin and cancellation scrapers."""
import unittest
from monitor import parse_official_news_table, parse_official_pdf_links, parse_official_bulletins


class EuroAreaSourceTests(unittest.TestCase):

    def test_malta_news_table_isolation(self):
        html = """
        <table><tr><th>Title</th><th>Date</th><th></th></tr>
        <tr><td>Philately - Special Handstamp - UNESCO Anniversary</td>
            <td>16/11/2026</td><td><a href="/news-details?id=6557">Go to Article</a></td></tr>
        <tr><td>Temporary Closure of Post Office</td>
            <td>17/11/2026</td><td><a href="/news-details?id=6558">Go to Article</a></td></tr>
        <tr><td>Philately - Special Handstamp - Other</td>
            <td>28/10/2025</td><td><a href="/news-details?id=6000">Go to Article</a></td></tr>
        </table>
        """
        source = dict(id="malta-special-handstamps", name="MaltaPost",
                      url="https://www.maltapost.com/news?l=1",
                      row_pattern=r"Special\s+Hand\s*stamp",
                      min_year=2026, max_entries=8, category="Sonderstempel")
        results = parse_official_news_table(html, source)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "https://www.maltapost.com/news-details?id=6557")
        self.assertIn("UNESCO Anniversary", results[0]["title"])
        self.assertEqual(results[0]["published"], "News published: 16/11/2026")
        self.assertNotIn("Closure", results[0]["title"])

    def test_pdf_bulletins_use_link_url_not_neighboring_text(self):
        html = """
        <div><h3>2026</h3><a href="/getmedia/a/Philatelux_2026_09_EN.pdf">Download</a>
             <a href="/en-US/Page/Newsletter">Join the newsletter</a>
             <a href="/getmedia/b/Philatelux_2026_05_EN.pdf">Download</a></div>
        """
        source = dict(id="luxembourg-philatelux", name="POST Luxembourg",
                      url="https://www.postphilately.lu/en-US/Page/Philatelux",
                      url_pattern=r"Philatelux[_-]20\d{2}[_-]\d{2}[^/?]*\.pdf(?:$|\?)",
                      max_entries=4, category="Philatelie")
        results = parse_official_pdf_links(html, source)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Philatelux 2026 09 EN")
        self.assertEqual(results[0]["url"], "https://www.postphilately.lu/getmedia/a/Philatelux_2026_09_EN.pdf")

    def test_slovenia_bulletin_links_only(self):
        html = '<a href="/PersonalSite/bulletins/Bulletin-163.pdf">Bulletin 163</a>'
        source = dict(id="slovenia-bulletins", name="Pošta Slovenije",
                      url="https://en.posta.si/home/stamps/bulletins",
                      title_pattern=r"Bulletin\s+\d{2,3}", pdf_only=True,
                      max_entries=3, category="Philatelie")
        results = parse_official_bulletins(html, source)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Bulletin 163")


if __name__ == "__main__":
    unittest.main()
