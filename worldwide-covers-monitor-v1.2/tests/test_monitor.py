import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor import parse_feed, parse_deutschepost_page, normalize_url, is_relevant

SOURCE={"id":"test","name":"Test Feed","kind":"rss","category":"Philatelie"}

class MonitorTests(unittest.TestCase):
    def test_rss(self):
        fixture=(Path(__file__).resolve().parents[1]/'fixtures'/'rss.xml').read_bytes()
        entries=parse_feed(fixture,SOURCE)
        self.assertEqual(2,len(entries))
        self.assertTrue(is_relevant(entries[0],SOURCE,['polar','philatelic cover']))
        self.assertFalse(is_relevant(entries[1],SOURCE,['polar','philatelic cover']))

    def test_atom(self):
        xml=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>New stamp</title><link href="https://example.com/x"/><summary>New postal item</summary></entry></feed>'
        self.assertEqual(parse_feed(xml,SOURCE)[0]['url'],'https://example.com/x')

    def test_post_issue(self):
        src=dict(SOURCE,kind='edition_page',url='https://example.com/deutschepost')
        one=parse_deutschepost_page('<p>Ausgabe 24-2026 | 04. November</p>',src)[0]
        two=parse_deutschepost_page('<p>Ausgabe 25-2026 | 18. November</p>',src)[0]
        self.assertNotEqual(one['id'],two['id'])
        self.assertEqual(one['url'],src['url'])

    def test_tracking_removed(self):
        self.assertEqual(normalize_url('https://example.org/x/?utm_source=abc&abc=1#section'), 'https://example.org/x?abc=1')

if __name__=='__main__': unittest.main()

class OfficialBulletinTests(unittest.TestCase):
    def setUp(self):
        from monitor import parse_official_bulletins
        self.parse = parse_official_bulletins

    def test_swiss_philanews_links(self):
        source = {"id":"ch", "name":"Schweiz", "url":"https://www.post.ch/briefmarken", "category":"Sonderstempel", "title_pattern":r"PhilaNews\s*\d{1,2}\s*/\s*20\d{2}", "pdf_only":True,"max_entries":2}
        page = '''<div><a href="/files/news-11.pdf">PhilaNews 11/2026 (PDF)</a><a href="/files/news-10.pdf">PhilaNews 10/2026 (PDF)</a></div>'''
        entries=self.parse(page,source)
        self.assertEqual(2,len(entries))
        self.assertEqual(entries[0]['title'],'PhilaNews 11/2026')
        self.assertEqual(entries[0]['url'],'https://www.post.ch/files/news-11.pdf')

    def test_australia_heading_and_pdf(self):
        source={"id":"au","name":"Australia Post","url":"https://collectables.auspost.com.au/list","category":"Philatelie","title_pattern":r"Stamp Bulletin\s+\d+","pdf_only":True,"max_entries":2}
        page='''<h4>Stamp Bulletin 404</h4><a href="/files/404.pdf">Download (PDF, 6MB)</a><h4>Stamp Bulletin 403</h4><a href="/files/403.pdf">Download</a>'''
        entries=self.parse(page,source)
        self.assertEqual([e['title'] for e in entries],['Stamp Bulletin 404','Stamp Bulletin 403'])

    def test_austria_context(self):
        source={"id":"at","name":"Post AT","url":"https://www.post.at/p/c/sonderpostaemter","title_pattern":r"Sonderpostämter\s+20\d{2}","category":"Sonderstempel","pdf_only":True,"max_entries":1}
        page='<div><p>Sonderpostämter 2026</p><p>pdf, 6 mb</p><a href="https://assets.post.at/stempel-2026.pdf">Download</a></div>'
        self.assertEqual(self.parse(page,source)[0]['title'],'Sonderpostämter 2026')

    def test_royal_mail_anchor(self):
        source={"id":"uk","name":"Royal Mail","url":"https://www.royalmail.com/postmarks","title_pattern":r"(?:Download (?:the )?latest )?Postmark Bulletin","category":"Sonderstempel","pdf_only":True,"max_entries":1}
        page='<p>Postmarks</p><a href="/media/postmark-bulletin.pdf">Download the latest Postmark Bulletin</a>'
        self.assertEqual(self.parse(page,source)[0]['url'],'https://www.royalmail.com/media/postmark-bulletin.pdf')
