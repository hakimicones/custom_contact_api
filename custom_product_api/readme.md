# Custom Product API

Module Odoo indépendant exposant les routes `GET /api/v1/products` et
`POST /api/v1/products/list` pour consulter les modèles de produits actifs.
L'API utilise une clé distincte de celle de l'API contacts.

## Installation et configuration

1. Placez le dossier `custom_product_api` dans un répertoire d'addons Odoo.
2. Mettez à jour la liste des applications et installez **Custom Product API**.
3. Dans **Paramètres > Technique > Paramètres système**, définissez
   `custom_product_api.api_key` avec une valeur secrète longue et aléatoire.
   Envoyez cette valeur dans l'en-tête `X-API-Key` et utilisez HTTPS en
   production.

Si la clé n'est pas configurée, l'API refuse les requêtes. Le module dépend
du module Odoo `product`.

## Lister les produits

```bash
curl "https://odoo.example.com/api/v1/products?limit=50&offset=0" \
  -H "X-API-Key: VOTRE_CLE_API"
```

La réponse contient `products`, `total`, `limit` et `offset`. Chaque produit
contient son identifiant, son nom, sa référence interne, son code-barres, son
prix de vente et sa catégorie. Les produits archivés sont exclus par le
comportement standard d'Odoo.

La pagination est de 50 éléments par défaut. `limit` accepte une valeur entre
1 et 100 et `offset` une valeur supérieure ou égale à 0.

Les erreurs de paramètres retournent `400`, une clé invalide `401`, et une
erreur interne `500`.
