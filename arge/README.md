# ARGE Polarphilatelie – Einbindung in WordPress

Die ARGE-Ansichten sind **eigenständige Oberflächen**, aber keine separaten Datenbestände.

- Atlas: \`/arge/polar/\` – nutzt direkt \`/polar/stations.json\` und \`/polar/land.json\` (derzeit 58 Stationen/Orte). Die ARGE-Oberfläche ist deutschsprachig, die redaktionellen Stationsbeschreibungen in der gemeinsamen Datenbank sind teilweise noch englisch.
- Portoliste: \`/arge/portoliste/\` – liest bei jedem Seitenaufruf \`/postage/rates.json\` und wählt **exakt 33** vorab festgelegte Länder/Postgebiete anhand eindeutiger Tarif-IDs. Länder, die später in der internationalen Datenbank ergänzt werden, erscheinen **nicht** ohne Änderung dieser Whitelist.
- Alle Daten, Quellenlinks und Aktualisierungsinformationen sind öffentlich. **Keine internen ARGE-Adressen oder nur für Mitglieder bestimmten Beschaffungstipps ergänzen.**

## GitHub Pages (nach Merge und erfolgreichem Workflow)

Atlas: https://aylien026.github.io/worldwide-cover-monitor/arge/polar/

Portoliste: https://aylien026.github.io/worldwide-cover-monitor/arge/portoliste/

Der GitHub-Actions-Workflow \`.github/workflows/monitor.yml\` kopiert die beiden Seiten ins Pages-Artefakt. Änderungen unter \`arge/**\`, \`polar/**\` und \`postage/**\` lösen ein neues Deployment aus. Der vorhandene Monitor-Job überwacht **philatelistische Nachrichtenquellen**, nicht automatisch sämtliche Portotarife. Die Portoliste aktualisiert sich automatisch, **wenn die gemeinsame JSON-Datei aktualisiert und von Pages veröffentlicht wurde**. Das ist nicht gleichbedeutend mit einer automatischen Tarifvalidierung bei jeder Postverwaltung.

## WordPress: Karte (bestehende Seite /karte/)

Im WordPress-Editor einen Block *Individuelles HTML* verwenden. Vorher den alten Karten-Code auf dieser Seite sichern:

\`\`\`html
<div style="width:100%;max-width:1200px;margin:0 auto;">
  <iframe id="arge-atlas" title="Interaktiver Polar Atlas der ARGE Polarphilatelie"
    src="https://aylien026.github.io/worldwide-cover-monitor/arge/polar/"
    loading="lazy" referrerpolicy="strict-origin-when-cross-origin"
    style="width:100%;display:block;min-height:1700px;border:0;background:white"></iframe>
</div>
\`\`\`

## WordPress: Portoliste (bestehende Seite /portoliste/)

Den bisherigen Tarif-Tabellenblock zunächst sichern, dann stattdessen:

\`\`\`html
<div style="width:100%;max-width:1200px;margin:0 auto;">
  <iframe id="arge-porto" title="Portoliste der ARGE Polarphilatelie"
    src="https://aylien026.github.io/worldwide-cover-monitor/arge/portoliste/"
    loading="lazy" referrerpolicy="strict-origin-when-cross-origin"
    style="width:100%;display:block;min-height:2100px;border:0;background:white"></iframe>
</div>
\`\`\`

### Optional: automatische iFrame-Höhe (falls WordPress Skripte erlaubt)

Das Skript *einmalig* auf der jeweiligen WordPress-Seite im HTML-Block unter dem iFrame ergänzen. Nur Größenmeldungen vom eigenen GitHub-Pages-Ursprung werden verarbeitet:

\`\`\`html
<script>
window.addEventListener('message', function(e) {
  if (e.origin !== 'https://aylien026.github.io' || !e.data) return;
  const map = { ARGE_ATLAS_HEIGHT: 'arge-atlas', ARGE_POSTAGE_HEIGHT: 'arge-porto' };
  const id = map[e.data.type];
  const el = id && document.getElementById(id);
  const h = Number(e.data.height);
  if (el && Number.isFinite(h) && h >= 250 && h <= 15000) el.style.height = h + 'px';
});
</script>
\`\`\`

Falls WordPress das Skript entfernt, bleiben die iFrames mit fester Mindesthöhe funktionsfähig. Bei sehr langen geöffneten Details können dann interne Scrollbalken auftreten. Ein einzelner HTML-Block mit beiden iFrames ist nicht erforderlich: Atlas und Portoliste gehören auf ihre jeweils bestehende WordPress-Unterseite.

## Fachliche Grenzen und Qualität

- **Postgebiete:** Der alte ARGE-Listeneintrag „Südgeorgien / Südshetlandinseln“ vermischt zwei unterschiedliche geografische/postalische Gebiete. Die neue Ansicht enthält daher nur Südgeorgien und Südliche Sandwichinseln und erklärt diese Korrektur.
- **AAT und Ross Dependency:** Die aktuellen Einträge sind ausdrücklich vorläufig / aus anderen Tarifen abgeleitet, keine bestätigten Postgebühren für die Stationen.
- **BAT:** Die hinterlegte amtliche Tarifabbildung für das britische Antarktis-Territorium stammt aus 2025; ein neuerer BAT-spezifischer Tarif kann nicht ausgeschlossen werden.
- **Luft/See/Postkarte:** Die internationale Datenbank erfasst Standard-, Economy- und Priority-Tarife, nicht systematisch getrennte Brief- und Postkartenpreise für Luft- und Seepost. Deshalb werden fehlende Unterschiede nicht erfunden.
- **Koordinaten:** Der Atlas ist ein kuratiertes Verzeichnis, keine Navigationskarte. Die Stationen auf Schelfeis können ihre Koordinaten verändern; die Anzeige übernimmt Quellenhinweise aus der gemeinsamen Datenbank.
- **Datenschutz:** Open-Meteo-Anfragen laufen im Besucherbrowser; externe Webcams können Verbindungsdaten verarbeiten. Die Datenschutzhinweise der WordPress-Site sollten dies berücksichtigen.

## Redaktioneller Ablauf

1. Bei einem offiziellen Tarifwechsel den passenden Eintrag in \`postage/rates.json\` einschließlich Quelle, Zielregion, Gewicht, Datum und Prüfstatus ändern bzw. durch vorhandene kontrollierte Prozesse aktualisieren.
2. Der bestehende Pages-Workflow veröffentlicht das JSON neu. Beim nächsten Aufruf laden beide Portolisten dieselben Daten.
3. Stationsänderungen ausschließlich in \`polar/stations.json\` pflegen. Danach verwenden beide Atlas-Oberflächen denselben neuen Stationsstand.
4. Größere Karten-UI-Änderungen müssen aktuell für **beide** HTML-Oberflächen (\`polar/index.html\` und \`arge/polar/index.html\`) gesondert geprüft werden. Die Daten sind zentral, die Oberflächentexte sind es nicht.
