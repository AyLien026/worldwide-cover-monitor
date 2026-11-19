# Worldwide Covers Monitor · Version 1.2

**Ein kleiner, unabhängiger Beobachtungsdienst für philatelistische Meldungen.**

Er prüft öffentliche Quellen, filtert thematisch passende Einträge, erkennt bereits bekannte Links, führt ein durchsuchbares HTML-Archiv und kann neue Funde optional per Zulip-Bot melden. Ein Betrieb **ohne eigenen Server** ist via GitHub Actions + GitHub Pages möglich.

## Sofort ansehen

Die Datei `index.html` im Browser öffnen. Das Archiv funktioniert auch offline. Zu Beginn ist die Liste bewusst leer: Es werden **keine erfundenen oder als aktuell ausgegebenen Testmeldungen** angezeigt. Der Quellenabruf füllt die Liste.

## Für automatische Aktualisierungen: GitHub

1. Ein neues GitHub-Repository erstellen, z. B. `worldwide-covers-monitor` (am einfachsten öffentlich, ohne private Daten).
2. **Den entpackten Inhalt dieses ZIP-Archivs** hochladen, sodass `.github/workflows/monitor.yml`, `monitor.py` und `index.html` im Stammverzeichnis liegen, **nicht** in einem zusätzlichen Unterordner. Versteckte Ordner wie `.github` müssen mit übertragen werden (Finder am Mac: `⌘` + `⇧` + `.` zeigt versteckte Dateien an). Das ZIP **nicht als einzelne Datei** hochladen.
3. Unter **Settings → Pages → Build and deployment → Source** unbedingt **GitHub Actions** auswählen (nicht `Deploy from a branch`, denn von Workflows mit `GITHUB_TOKEN` gepushte Commits starten keinen GitHub-Pages-Build).
4. In GitHub unter **Actions** den Workflow „Worldwide Covers Monitor“ mit **Run workflow** einmal manuell starten. Der erste Lauf baut den Datenbestand auf, lädt die aktualisierten JSON/JS-Daten hoch und veröffentlicht anschließend die HTML-Seite. Prüfen, ob beide Jobs `monitor` und `deploy` grün sind.
5. Danach prüft GitHub Actions die Quellen täglich gegen 08:37 Uhr (Europe/Berlin), sofern der Workflow aktiv bleibt. GitHub garantiert nicht die exakte Startminute. In öffentlichen Repositories können geplante Workflows nach 60 Tagen ohne Repository-Aktivität automatisch deaktiviert werden.

**Wichtig:** Ein GitHub-Account ist hier noch nicht verbunden. Die ZIP-Datei ist bereit, aber ich habe keine Dateien in dein GitHub-Konto hochgeladen und keine öffentliche Website veröffentlicht. Auch ist im Erstellungscontainer keine Verbindung zu den Live-Feeds möglich; der reale Erstabruf muss in GitHub oder auf einem verbundenen Rechner erfolgen.

## Optional: Auf eigenem Rechner

Python **3.9 oder neuer** verwenden und im entpackten Ordner `python3 monitor.py` ausführen. Es werden ausschließlich Python-Standardbibliotheken benutzt. Das Archiv kann man danach lokal öffnen. Für ältere macOS-Versionen ist Python 3 ggf. gesondert nötig. Der automatische Hintergrundbetrieb über GitHub ist meist einfacher.

Ein reiner Parser-Test ohne Internet geht mit `python3 -m unittest discover -s tests -v` (aktuell acht Tests). Die mitgelieferte `fixtures/rss.xml` enthält ausschließlich als Demo markierte Beispiele. Bei Quellenfehlern bricht der Monitor nicht vollständig ab, sondern protokolliert sie in `data/state.json`.

## Internationale Postverwaltungen und offizielle Bulletins

**Version 1.2** enthält acht aktivierte offizielle Informationsquellen mit eigenen Adaptern:

| Postverwaltung | Veröffentlichung | Was der technische Monitor erkennt |
|---|---|---|
| Deutsche Post | Stempel und Informationen | neue Ausgabennummer auf der Übersichtsseite |
| USPS, USA | Postal Bulletin | neue fortlaufende Ausgaben anhand der PDF-URLs; *Pictorial Postmarks* sind darin enthalten, werden aber nicht einzeln extrahiert |
| Royal Mail, UK | Postmark Bulletin | verlinktes aktuelles PDF und Änderungen desselben PDFs per Prüfsumme |
| Schweizer Post | PhilaNews | neue Monats-PDFs mit Sonder- und Letzttagsstempeln |
| Schweizer Post | Die Lupe | neue PDF-Ausgaben des Sammlermagazins |
| Österreichische Post | Sonderpostämter | aktuelle Jahres-PDF und inhaltliche Aktualisierungen |
| Österreichische Post | Philatelietage | aktuelle Jahres-PDF und inhaltliche Aktualisierungen |
| Australia Post | Stamp Bulletin | neue Ausgaben anhand verlinkter PDFs |

Zusätzlich bleiben die vorhandenen allgemeinen RSS-Quellen aktiviert. Mehrere weitere **offizielle Referenzquellen** sind in `sources.json` samt Original-URL verzeichnet, werden aber **noch nicht automatisch in das Webarchiv eingelesen**: Åland Post (Orts- und Motivstempel einschließlich Märket), Canada Post (Details / Stamp Catalogue), NZ Post Collectables (Ross Dependency), An Post (Irland), PostNord Schweden. Diese Unterscheidung ist bewusst: Eine offizielle Webseite ist nicht automatisch ein zuverlässig auswertbarer Feed.

**Ablauf:** Eine neue Ausgabe wird als Link zum offiziellen Dokument erfasst. Die einzelnen Stempeldaten, Fristen und Einsendeanschriften müssen bislang **im Original** geprüft werden, besonders bei PDFs. Für Royal Mail und die beiden österreichischen Jahres-PDFs prüft der Monitor außerdem einen PDF-Inhaltshash, damit geänderte Stempelübersichten unter gleichbleibender URL nicht übersehen werden. Das kostet zusätzliche Abrufe (jeweils bis max. 25 MB).

**Bitte beachten:** Die neuen offiziellen Quellen sind anhand der offiziellen Webseiten recherchiert und Parser-Funktionen wurden mit lokalen Testbeispielen geprüft. Ein echter Live-Test sämtlicher Quellseiten über Python konnte in der Erstellungsumgebung nicht ausgeführt werden. Änderungen an Seitenstrukturen, Anti-Bot-Schutz oder blockierte PDF-Abrufe können Fehler erzeugen; prüfe den ersten GitHub-Actions-Lauf unter `data/state.json`. Der USPS-Nummernbereich in `sources.json` ist für Ende 2026 vorkonfiguriert und muss für Folgejahre angepasst werden. Alle Referenzquellen können auch ohne Monitor einzeln über die Oberfläche geöffnet werden.

Die Nachrichten werden nach Schlagwörtern gefiltert, außer bei offiziellen Heften, die als Gesamtausgabe erfasst werden. Diese Methode kann Meldungen übersehen oder unpassende aufnehmen. Quelleninhalte werden nicht vollständig gespiegelt. Das Archiv ist auf 400 Fundstücke begrenzt.

## Optional: Zulip-Bot

Der Monitor funktioniert **ohne** Zulip. Wenn du Nachrichten zusätzlich in einen Zulip-Kanal schicken möchtest:

1. Einen Zulip-Bot mit API-Key erstellen und einen Kanal für die Meldungen vorbereiten.
2. In GitHub unter Repository → **Settings → Secrets and variables → Actions** diese Secrets anlegen:
   `ZULIP_SITE` (z. B. `https://beispiel.zulipchat.com`), `ZULIP_BOT_EMAIL`, `ZULIP_API_KEY`, `ZULIP_CHANNEL` (Name des Kanals).
3. Bei neuen Meldungen verschickt die Integration die Original-Links und Überschriften; der erste Bestandslauf soll keine Nachrichtenflut auslösen. Der Bot benötigt Schreibrechte für den Kanal.

**Sicherheit:** Niemals API-Schlüssel in `sources.json` oder andere Dateien schreiben. GitHub Pages veröffentlicht die Archivdaten; keine Privatanschriften, nicht öffentlichen Kontakte oder persönliche Nachrichten darin ablegen.

## Was Version 1 noch nicht kann

- Keine automatisierte Überprüfung, ob eine reale Poststelle Sammlerpost annimmt.
- Keine KI-Klassifikation oder semantische Dublettenprüfung. Gleichartige Meldungen mit verschiedenen Links können mehrfach auftauchen.
- Kein gemeinschaftliches Online-Bearbeiten von Einträgen. *Vorgemerkt* und *Gelesen* werden ausschließlich lokal im jeweiligen Browser gespeichert.
- Kein automatisches Extrahieren der Stempeltermine aus PDF-Heften.
- Keine garantierte Verfügbarkeit aller Feeds: Bei geänderten Quellformaten muss die Konfiguration angepasst werden.

## Technisches Konzept

`Offizielle Bulletins (HTML/PDF-Link) oder RSS → Parser → URL-/PDF-Hash zur Dublettenprüfung → JSON-Archiv → HTML-Oberfläche → optional Zulip-API`.

Das Quellenarchiv ist das technische Projekt; die zusätzlich in ChatGPT eingerichtete tägliche Recherche läuft unabhängig davon und speist dieses JSON-Archiv **nicht automatisch**.


## Country Explorer (public postage reference + collecting links)

The main Pages deployment now includes three connected public views:

- **Country Explorer:** `https://aylien026.github.io/worldwide-cover-monitor/countries/` — search countries and postal territories, inspect source-reviewed and unverified postal rates, see destination zones and announced changes, open official postal tariff sources, and search the public Worldwide Covers blog for related covers.
- **Postage Rates:** `https://aylien026.github.io/worldwide-cover-monitor/postage/` — detailed international postage directory.
- **Philatelic Bulletin Monitor:** `https://aylien026.github.io/worldwide-cover-monitor/` — publicly sourced philatelic bulletin archive.

The Explorer reads the **same** `postage/rates.json` as the postage directory. It does not maintain a second copy of tariffs. The deployment workflow copies `countries/index.html` to GitHub Pages and includes `countries/**` in its push triggers. The optional "Related monitor entries" section reads `data/items.json`, but only shows entries associated with the country of the publishing source; a bulletin link does **not** prove a collector can request a specific postmark.

**Visible data policy:** Unpriced research records remain in `postage/rates.json`, but are excluded from both public country lists. A numeric tariff can still be marked *Unverified*; neither a detected number nor a previously source-reviewed tariff should be treated as an unquestionable current counter price. There is no public listing of confidential addresses or private philatelic working-group information.

### Blogger embedding

A Blogger page can embed the Explorer using the HTML view:

```html
<div style="width:100%;max-width:1200px;margin:0 auto;">
  <iframe
    src="https://aylien026.github.io/worldwide-cover-monitor/countries/"
    title="Worldwide Covers Country Explorer"
    style="display:block;width:100%;min-height:1100px;border:0;background:#fff;"
    loading="lazy"
    referrerpolicy="strict-origin-when-cross-origin">
  </iframe>
</div>
```

The Explorer automatically hides its introductory hero when embedded in an iframe to avoid duplicating the host Blogger page heading. Blogger does not automatically create a navigation/menu entry: it must be added in the blog's **Pages / Layout** controls. The iframe has a fixed minimum height because Blogger and GitHub Pages are different origins and cannot safely auto-resize one another without an additional integration.

Direct URL to a country: `/countries/?country=Japan` (country names in query parameters are URL-encoded). The blog cover link opens a **search** on Worldwide Covers; it does not assert a matching existing article. Official source links can change over time.
