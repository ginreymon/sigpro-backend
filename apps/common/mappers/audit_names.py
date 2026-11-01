from django.contrib.auth.models import User

AUDIT_ID_FIELDS = {"created_by_id": "created_by_name", "updated_by_id": "updated_by_name"}


def _walk(node, visit):
    if isinstance(node, dict):
        visit(node)
        node = list(node.values())
    if isinstance(node, list):
        for child in node:
            _walk(child, visit)


def add_audit_names(data):
    """Add `created_by_name` / `updated_by_name` next to every `created_by_id` / `updated_by_id`
    found at any depth of a JSON-like structure (mutates it in place, one query for all users)."""
    ids = set()

    def collect(item):
        ids.update(item[f] for f in AUDIT_ID_FIELDS if item.get(f) is not None)

    _walk(data, collect)
    if not ids:
        return data

    # Full name when present, username otherwise.
    names = {
        u.id: u.get_full_name().strip() or u.username
        for u in User.objects.filter(id__in=ids).only("id", "username", "first_name", "last_name")
    }

    def fill(item):
        for id_field, name_field in AUDIT_ID_FIELDS.items():
            if id_field in item:
                item[name_field] = names.get(item[id_field])

    _walk(data, fill)
    return data
