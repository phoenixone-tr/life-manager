# Life Manager – Learnings & Gotchas

Gesammelte Erkenntnisse aus der Entwicklung, damit wir (und zukünftige Agents) nicht in die gleichen Fallen tappen.

---

## Infrastruktur

### SSH-Zugriff

- **Port 2922**, nicht 22. Aliases `ssh vm-services` / `ssh vm-nginx` nutzen.
- User `claude-admin`, Key-basiert. Keys müssen mit `claude-ssh-start` geladen werden – das kann nur Martin, nicht der Agent.
- **Sudo auf VM 211:** Nur für Docker-Befehle erlaubt. Kein `sudo mkdir`, kein Filesystem-sudo. Neue Verzeichnisse unter `/opt/docker/` muss Martin anlegen.
- **Sudo auf VM 200:** Nur `nginx -t`, `tee` für sites-available, `ln -s` für sites-enabled, `systemctl reload/restart nginx`.
- **SSH mit sudo über nicht-interaktives SSH** (`ssh vm-services "sudo ..."`) schlägt fehl mit "a terminal is required". Lösung: `claude-admin` ist in der `docker`-Gruppe, also Docker-Befehle direkt ohne `sudo` ausführen.

### Docker

- **Service-Namen** im `docker-compose.yml` entsprechen nicht den Container-Namen. Compose-Service heißt `fastapi`, Container heißt `lm-api`. Immer `docker compose config --services` prüfen.
- **Qdrant Docker Image** enthält absichtlich kein `curl`/`wget`. Healthcheck muss über Bash erfolgen:
  ```yaml
  healthcheck:
    test: ["CMD-SHELL", "bash -c 'echo -n > /dev/tcp/127.0.0.1/6333'"]
  ```
- **Docker-interne DNS** (z.B. `http://lm-api:8000`) funktioniert nur innerhalb desselben Docker-Netzwerks. n8n läuft in einem separaten Stack → Host-IP verwenden: `http://10.10.10.211:8000`.

### DNS & SSL

- **Wildcard-Zertifikate** decken nur eine Ebene ab: `*.martin-mueller-ki.de` deckt NICHT `api.life.martin-mueller-ki.de` ab. Für Sub-Subdomains braucht man ein separates Zertifikat für `*.life.martin-mueller-ki.de`.
- **FritzBox DNS-Cache** ist aggressiv. Nach DNS-Änderungen auf dem Mac flushen:
  ```bash
  sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
  ```
- **acme.sh und sudo:** `acme.sh` verweigert die Ausführung unter `sudo`. Man muss erst `sudo -i` machen und dann als root direkt ausführen.
- **acme.sh Default-CA:** Seit einem Update ist ZeroSSL der Standard. Für Let's Encrypt explizit angeben:
  ```bash
  acme.sh --issue ... --server letsencrypt
  ```
- **IONOS DNS API** für DNS-Challenge: Credentials stehen in `~/.acme.sh/account.conf` (IONOS_Token, IONOS_API Format: `prefix.secret`).

---

## n8n Workflow

### Outlook Trigger

- Der Microsoft Outlook Trigger feuert standardmäßig bei **allen Nachrichten** (auch gesendeten!). Fix: Unter **Filters → Folders to Include** den Ordner **"Posteingang"** auswählen.
- Das muss bei **beiden** Triggern gesetzt werden (Business + Family).

### Set-Node: "Include Other Input Fields"

- Der n8n Set-Node (v3.4) hat standardmäßig **"Include Other Input Fields" auf OFF**. Das bedeutet: nur die explizit gesetzten Felder werden weitergegeben, alle Eingangsdaten gehen verloren.
- **Immer "Include Other Input Fields" auf ON setzen**, wenn man ein Feld hinzufügen will, ohne die bestehenden Daten zu verlieren.

### Filter-Node und Arrays

- Der n8n Filter-Node mit Operator `contains` funktioniert **nicht** mit Arrays als Input. Die Expression `{{ $json.actions }}` liefert ein Array, aber `contains` erwartet einen String.
- **Lösung:** JavaScript-Expression verwenden:
  ```
  {{ $json.actions.includes('notify_telegram') }}
  ```
  Mit Operator `is true` (Boolean).

### HTTP Request Node

- Die **Response** eines HTTP Request Nodes ersetzt die gesamte `$json`-Daten. Originaldaten vom Trigger sind danach nicht mehr verfügbar.
- **Lösung:** API-Response um die benötigten Input-Felder erweitern (Email-Echo-Pattern), statt in n8n komplizierte Merge-Logik zu bauen.

### n8n Credentials

- Credentials werden beim **JSON-Export nicht mitexportiert**. Nach dem Import müssen sie manuell zugewiesen werden.
- In der **Community Edition** können Credential-Namen nicht umbenannt werden.

---

## Telegram Bot API

### Parse Mode

- **HTML:** Sehr strikt. Emojis und Sonderzeichen wie `<>` (leere E-Mail-Adresse) werden als HTML-Tags interpretiert → `"Unsupported start tag"` Fehler.
- **MarkdownV2:** Extrem empfindlich. Zeichen `_ * [ ] ( ) ~ > # + - = | { } . !` müssen **alle** escaped werden. Bei dynamischem Content (E-Mail-Betreffs etc.) quasi unmöglich wartbar.
- **Markdown (Legacy):** Beste Wahl für dynamischen Content. Nur `_ * ` [ ` müssen escaped werden. Tolerant gegenüber `-`, `=`, `.`, `(`, `)` etc.
- **"Chat not found" Fehler:** Der User muss dem Bot **zuerst eine Nachricht schicken** (`/start`), bevor der Bot Nachrichten senden kann.

### Escaping für Markdown (Legacy)

```javascript
const esc = (s) => s.replace(/([_*`\[])/g, '\\$1');
```

---

## FastAPI / Pydantic

### n8n-Kompatibilität

- n8n sendet für fehlende Felder **leere Strings** statt `null`. Ein `datetime`-Feld das `""` empfängt schlägt bei Pydantic fehl.
- **Lösung:** `@field_validator` mit `mode="before"` der leere Strings zu `None` konvertiert:
  ```python
  @field_validator("received_at", mode="before")
  @classmethod
  def empty_string_to_none(cls, v):
      if v == "" or v is None:
          return None
      return v
  ```
- Alle Request-Felder sollten **Defaults** haben (`Field("")`, `Field(False)`, etc.), damit n8n auch unvollständige Payloads schicken kann.

### Email-Echo Pattern

- Die Classify-API gibt die Input-Felder als `email`-Objekt in der Response zurück. So hat der n8n Format-Node alle Daten in einem einzigen JSON, ohne auf vorherige Nodes referenzieren zu müssen.
- Zugriff in n8n: `$json.email.from_address`, `$json.email.subject`, etc.

---

## Entwicklungsworkflow

### Lokale Tests

- Tests brauchen `PYTHONPATH=services/api` und `TELEGRAM_BOT_TOKEN=test-token`:
  ```bash
  cd /Users/martinmueller/Development/life-manager
  PYTHONPATH=services/api TELEGRAM_BOT_TOKEN=test-token python -m pytest services/api/tests/ -v
  ```

### Deployment-Ablauf

1. Lokal committen und pushen
2. `ssh vm-services "cd /opt/docker/life-manager && git pull origin main"`
3. `ssh vm-services "cd /opt/docker/life-manager && docker compose up -d --build fastapi"` (kein sudo nötig)
4. Smoke-Test: `ssh vm-services 'curl -s http://localhost:8000/health'`

---

*Letzte Aktualisierung: 2026-02-14*
