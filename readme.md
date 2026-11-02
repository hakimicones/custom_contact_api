# Custom Contact API

Module Odoo exposant `POST /api/v1/contacts` pour créer un contact
(`res.partner`) au moyen d'un corps JSON et d'une clé API.

## Installation et configuration

1. Placez le dossier du module dans un répertoire d'addons Odoo et mettez à
   jour la liste des applications.
2. Installez **Custom Contact API**.
3. Dans **Paramètres > Technique > Paramètres système**, définissez la clé
   `custom_contact_api.api_key` avec une valeur secrète longue et aléatoire.
   Cette valeur est envoyée dans l'en-tête `X-API-Key`. Ne la placez pas dans
   le code source et utilisez HTTPS en production.

Si la clé n'est pas configurée, l'endpoint refuse les requêtes.

## Requête d'exemple

```bash
curl -X POST "https://odoo.example.com/api/v1/contacts" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: VOTRE_CLE_API" \
  -d '{
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "phone": "+33123456789",
    "mobile": "+33612345678",
    "company": "Analytical Engines"
  }'
```

Le champ `company` est facultatif. Lorsqu'il est fourni, l'API recherche une
entreprise (`res.partner` avec `is_company=True`) portant ce nom ou la crée,
puis rattache le contact à celle-ci.

Une création réussie retourne HTTP `201` et l'identifiant du contact. Les
erreurs de validation retournent `400`, une authentification incorrecte `401`,
un type de contenu incorrect `415`, et une erreur interne `500`.
