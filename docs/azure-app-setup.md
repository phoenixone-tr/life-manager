# Azure App-Registrierung für Life Manager (n8n Email-Zugriff)

## Übersicht

Eine Multi-Tenant App-Registrierung für zwei M365-Accounts:
- **M365 Business** (Organisationskonto)
- **M365 Family** (persönliches Microsoft-Konto)

n8n nutzt diese App, um Emails über Microsoft Graph API abzurufen.

---

## Schritt 1: Azure Portal öffnen

1. Gehe zu [https://portal.azure.com](https://portal.azure.com)
2. Logge dich mit dem **Business-Account** ein
3. Navigiere zu: **Microsoft Entra ID** → **App registrations**
   *(Früher "Azure Active Directory" → "App registrations")*

## Schritt 2: App registrieren

1. Klicke **+ New registration**
2. Ausfüllen:
   - **Name:** `Life Manager n8n`
   - **Supported account types:** Wähle die **dritte** Option:
     > *Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)*
   - **Redirect URI:**
     - Platform: **Web**
     - URI: `https://n8n-auto.martin-mueller-ki.de/rest/oauth2-credential/callback`
3. Klicke **Register**

**Notiere sofort:**
- **Application (Client) ID:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

## Schritt 3: Client Secret erstellen

1. In der App → **Certificates & secrets**
2. Klicke **+ New client secret**
   - **Description:** `n8n-life-manager`
   - **Expires:** 24 months
3. Klicke **Add**
4. **SOFORT den "Value" kopieren** (wird nur einmal angezeigt, nicht das "Secret ID"!)

**Notiere:**
- **Client Secret Value:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Schritt 4: API Permissions konfigurieren

1. In der App → **API permissions**
2. Klicke **+ Add a permission**
3. Wähle **Microsoft Graph** → **Delegated permissions**
4. Suche und aktiviere folgende Permissions:

| Permission | Zweck |
|-----------|-------|
| `Mail.Read` | Emails lesen |
| `Mail.ReadWrite` | Emails lesen + Entwürfe (Phase 2) |
| `Mail.Send` | Emails senden (später) |
| `User.Read` | Benutzer-Profil (Standard) |
| `offline_access` | Refresh-Token für dauerhaften Zugriff |
| `openid` | OpenID Connect |
| `profile` | Benutzer-Profil |

5. Klicke **Add permissions**
6. Klicke **Grant admin consent for [Tenant-Name]** (blauer Button oben)
7. Bestätige mit **Yes**

**Ergebnis:** Alle Permissions sollten einen grünen Haken unter "Status" haben.

> **Hinweis:** Admin Consent gilt nur für den Business-Tenant. Beim persönlichen Account wird der Consent beim ersten Login in n8n erteilt.

## Schritt 5: Zusammenfassung

Nach Abschluss hast du folgende Werte:

```
Application (Client) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Client Secret Value:     xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Redirect URI:            https://n8n-auto.martin-mueller-ki.de/rest/oauth2-credential/callback
```

Diese Werte brauchst du für die n8n Credential-Einrichtung (nächster Schritt).

---

## n8n Credentials einrichten

### Credential 1: M365 Business

1. Öffne n8n: [https://n8n-auto.martin-mueller-ki.de](https://n8n-auto.martin-mueller-ki.de)
2. Gehe zu **Settings** → **Credentials** → **Add Credential**
3. Suche nach: **Microsoft Outlook OAuth2 API**
4. Ausfüllen:
   - **Client ID:** (von Azure, Schritt 2)
   - **Client Secret:** (von Azure, Schritt 3)
5. Klicke **Sign in with Microsoft** (oder "Connect my account")
6. Logge dich mit dem **Business-Account** ein
7. Bestätige die Permissions im Consent-Dialog
8. **Name:** `M365 Business Email`
9. Klicke **Save**

### Credential 2: M365 Family

1. **Add Credential** → **Microsoft Outlook OAuth2 API**
2. Gleiche **Client ID** und **Client Secret** wie oben
3. Klicke **Sign in with Microsoft**
4. Logge dich mit dem **persönlichen/Family-Account** ein
5. Bestätige die Permissions
6. **Name:** `M365 Family Email`
7. Klicke **Save**

---

## Troubleshooting

### "Need admin approval"
- **Business-Account:** Admin Consent muss in Azure erteilt sein (Schritt 4.6)
- **Persönlicher Account:** Sollte ohne Admin Consent funktionieren

### Redirect URI Mismatch
- Die URI in Azure muss **exakt** mit der n8n Callback-URL übereinstimmen
- Prüfe: Kein trailing Slash, `https` nicht `http`
- Korrekt: `https://n8n-auto.martin-mueller-ki.de/rest/oauth2-credential/callback`

### Token Refresh schlägt fehl
- Prüfe ob `offline_access` in den API Permissions ist
- Ohne `offline_access` läuft der Token nach 1 Stunde ab

### n8n Callback-URL nicht erreichbar
Test: `curl -I https://n8n-auto.martin-mueller-ki.de/rest/oauth2-credential/callback`
Muss HTTP 200 oder 404 zurückgeben (nicht Connection Refused).

### Persönlicher Account: "Application not found in directory"
- Sicherstellen dass "Multi-tenant + personal accounts" gewählt wurde (Schritt 2)
- Nicht "Single tenant" oder "Multi-tenant only"
