import hmac
import json
import logging
import re

from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from psycopg2 import Error as PsycopgError


_logger = logging.getLogger(__name__)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_API_KEY_PARAMETER = "custom_contact_api.api_key"


def _json_response(payload, status):
    response = request.make_response(
        json.dumps(payload),
        headers=[("Content-Type", "application/json; charset=utf-8")],
    )
    response.status_code = status
    return response


def _optional_text(data, field, max_length):
    value = data.get(field)
    if value is None or value == "":
        return False
    if not isinstance(value, str):
        raise ValueError(f"'{field}' doit être une chaîne de caractères.")

    value = value.strip()
    if not value:
        return False
    if len(value) > max_length:
        raise ValueError(f"'{field}' ne doit pas dépasser {max_length} caractères.")
    return value


class ContactApiController(http.Controller):
    @http.route(
        "/api/v1/contacts",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def create_contact(self, **kwargs):
        configured_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param(_API_KEY_PARAMETER)
        )
        provided_key = request.httprequest.headers.get("X-API-Key", "")
        if not configured_key or not provided_key or not hmac.compare_digest(
            configured_key, provided_key
        ):
            return _json_response(
                {"error": "Authentification invalide."},
                401,
            )

        if not request.httprequest.is_json:
            return _json_response(
                {"error": "Le Content-Type doit être application/json."},
                415,
            )
        try:
            data = request.httprequest.get_json()
        except (BadRequest, UnsupportedMediaType):
            return _json_response({"error": "Le corps JSON est invalide."}, 400)

        if not isinstance(data, dict):
            return _json_response(
                {"error": "Le corps JSON doit être un objet."},
                400,
            )

        allowed_fields = {"name", "email", "phone", "mobile", "company"}
        unknown_fields = sorted(set(data) - allowed_fields)
        if unknown_fields:
            return _json_response(
                {
                    "error": "Des champs ne sont pas pris en charge.",
                    "fields": unknown_fields,
                },
                400,
            )

        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            return _json_response(
                {"error": "'name' est obligatoire et doit être une chaîne non vide."},
                400,
            )
        name = name.strip()
        if len(name) > 255:
            return _json_response(
                {"error": "'name' ne doit pas dépasser 255 caractères."},
                400,
            )

        try:
            email = _optional_text(data, "email", 254)
            phone = _optional_text(data, "phone", 64)
            mobile = _optional_text(data, "mobile", 64)
            company_name = _optional_text(data, "company", 255)
        except ValueError as error:
            return _json_response({"error": str(error)}, 400)

        if email and not _EMAIL_RE.fullmatch(email):
            return _json_response(
                {"error": "'email' n'a pas un format valide."},
                400,
            )

        try:
            # Keep company and contact creation atomic if either ORM operation fails.
            with request.env.cr.savepoint():
                partner_model = request.env["res.partner"].sudo()
                parent = False
                if company_name:
                    parent = partner_model.search(
                        [
                            ("name", "=", company_name),
                            ("is_company", "=", True),
                        ],
                        limit=1,
                    )
                    if not parent:
                        parent = partner_model.create(
                            {
                                "name": company_name,
                                "is_company": True,
                            }
                        )

                values = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "mobile": mobile,
                }
                if parent:
                    values["parent_id"] = parent.id
                partner = partner_model.create(values)
        except (
            AccessError,
            PsycopgError,
            UserError,
            ValidationError,
            ValueError,
        ):
            _logger.exception("Échec lors de la création d'un contact via l'API.")
            return _json_response(
                {"error": "Une erreur interne a empêché la création du contact."},
                500,
            )

        return _json_response(
            {
                "id": partner.id,
                "name": partner.name,
                "email": partner.email or None,
                "phone": partner.phone or None,
                "mobile": partner.mobile or None,
                "company": partner.parent_id.name or None,
            },
            201,
        )
