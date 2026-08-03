# Releases

Die kanonische Quelle jedes Stands ist der annotierte Git-Tag `v<VERSION>`.
`scripts/build.sh` erzeugt zusätzlich unter `dist/` ein strukturtreues Archiv
aus den getrackten Dateien von `HEAD` sowie ein Manifest mit SHA-256-Prüfsumme.

`dist/` wird nicht versioniert. Validierung, Build, lokaler Release-Tag,
Veröffentlichung und Deployment sind bewusst getrennte Vorgänge. Dadurch
verändert ein Prüf- oder Buildlauf weder Git-Historie noch Produktivsystem.
