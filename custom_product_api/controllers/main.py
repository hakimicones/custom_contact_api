import hmac
import json
import logging

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from psycopg2 import Error as PsycopgError


_logger = logging.getLogger(__name__)
_API_KEY_PARAMETER = "custom_product_api.api_key"


def _json_response(payload, status):
    response = request.make_response(
        json.dumps(payload),
        headers=[("Content-Type", "application/json; charset=utf-8")],
    )
    response.status_code = status
    return response


class ProductApiController(http.Controller):
    def _is_authenticated(self):
        configured_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param(_API_KEY_PARAMETER)
        )
        provided_key = request.httprequest.headers.get("X-API-Key", "")
        return bool(
            configured_key
            and provided_key
            and hmac.compare_digest(configured_key, provided_key)
        )

    def _products_response(self, limit, offset):
        try:
            product_model = request.env["product.template"].sudo()
            domain = []
            total = product_model.search_count(domain)
            records = product_model.search_read(
                domain,
                fields=[
                    "id",
                    "name",
                    "default_code",
                    "barcode",
                    "list_price",
                    "categ_id",
                ],
                offset=offset,
                limit=limit,
                order="id",
            )
        except (AccessError, PsycopgError, UserError, ValueError):
            _logger.exception("Échec lors de la lecture des produits via l'API.")
            return _json_response(
                {"error": "Une erreur interne a empêché la lecture des produits."},
                500,
            )

        products = [
            {
                "id": record["id"],
                "name": record["name"],
                "default_code": record["default_code"] or None,
                "barcode": record["barcode"] or None,
                "list_price": record["list_price"],
                "category": record["categ_id"][1] if record["categ_id"] else None,
            }
            for record in records
        ]
        return _json_response(
            {
                "products": products,
                "total": total,
                "limit": limit,
                "offset": offset,
            },
            200,
        )

    def _pagination_error(self, limit, offset):
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or isinstance(offset, bool)
            or not isinstance(offset, int)
        ):
            return _json_response(
                {"error": "'limit' et 'offset' doivent être des entiers."},
                400,
            )
        if limit < 1 or limit > 100 or offset < 0:
            return _json_response(
                {"error": "'limit' doit être entre 1 et 100 et 'offset' positif."},
                400,
            )
        return None

    @http.route(
        "/api/v1/products",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def list_products(self, **kwargs):
        if not self._is_authenticated():
            return _json_response({"error": "Authentification invalide."}, 401)

        args = request.httprequest.args
        try:
            limit = int(args.get("limit", 50))
            offset = int(args.get("offset", 0))
        except ValueError:
            return _json_response(
                {"error": "'limit' et 'offset' doivent être des entiers."},
                400,
            )
        pagination_error = self._pagination_error(limit, offset)
        if pagination_error:
            return pagination_error

        return self._products_response(limit, offset)
