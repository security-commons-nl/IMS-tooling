# Plan: Tenant-beheerpagina voor superusers

## Context

Een superuser kan momenteel tenants (organisaties) alleen via de API beheren — er is geen frontend-pagina voor. De backend endpoints bestaan al volledig (`/tenants/` CRUD + users + relationships). We bouwen een `/tenants` pagina die het bestaande users-page patroon volgt.

Scope: **alleen superusers** zien deze pagina (niet Beheerder).

---

## Bestanden

### Nieuw (2 bestanden)

| Bestand | Doel |
|---------|------|
| `frontend/ims/state/tenant.py` | TenantState — CRUD, leden-beheer, TenantRole wijzigen |
| `frontend/ims/pages/tenants.py` | Pagina met tabel, form-dialoog, leden-dialoog, delete-dialoog |

### Wijzigen (4 bestanden)

| Bestand | Wijziging |
|---------|-----------|
| `frontend/ims/api/client.py` | 8 tenant-methods toevoegen |
| `frontend/ims/state/auth.py` | `is_superuser` computed var toevoegen |
| `frontend/ims/components/layout.py` | "Organisaties" link in sidebar (superuser-only) |
| `frontend/ims/ims.py` | Pagina + state registreren |

### Backend (1 bestand)

| Bestand | Wijziging |
|---------|-----------|
| `backend/app/api/v1/endpoints/tenants.py` | `PATCH /{tid}/users/{uid}/role` endpoint toevoegen (TenantRole wijzigen) |

---

## Stap 1: Backend — TenantRole wijzigen endpoint

`backend/app/api/v1/endpoints/tenants.py` — nieuw endpoint toevoegen:

```
PATCH /tenants/{tenant_id}/users/{user_id}/role
Body: { "role": "ADMIN" }  # OWNER / ADMIN / MEMBER
Guard: require_admin (Beheerder only)
```

Zoekt de TenantUser, past `role` aan, commit.

## Stap 2: API Client uitbreiden

`frontend/ims/api/client.py` — 8 methods toevoegen:

- `get_tenants(skip, limit, is_active)` → GET /tenants/
- `create_tenant(data)` → POST /tenants/
- `update_tenant(id, data)` → PATCH /tenants/{id}
- `deactivate_tenant(id)` → DELETE /tenants/{id}
- `get_tenant_users(tid)` → GET /tenants/{tid}/users
- `add_user_to_tenant_by_tid(tid, uid)` → POST /tenants/{tid}/users/{uid}
- `remove_user_from_tenant_by_tid(tid, uid)` → DELETE /tenants/{tid}/users/{uid}
- `update_tenant_user_role(tid, uid, role)` → PATCH /tenants/{tid}/users/{uid}/role

## Stap 3: AuthState — `is_superuser` var

`frontend/ims/state/auth.py` — toevoegen:

```python
@rx.var
def is_superuser(self) -> bool:
    user = self.user
    if not user:
        return False
    return user.get("is_superuser", False)
```

## Stap 4: TenantState

`frontend/ims/state/tenant.py` — volgt UserState patroon:

**State vars:**
- `tenants: List[Dict]` — loaded tenants
- `tenant_users: List[Dict]` — users of selected tenant
- `all_users: List[Dict]` — all platform users (for add-to-tenant dropdown)
- `filter_active: str` — "ACTIEF" / "INACTIEF" / "ALLE"
- Form dialog: `show_form_dialog`, `is_editing`, `editing_tenant_id`
- Form fields: `form_name`, `form_slug`, `form_description`, `form_contact_email`, `form_is_active`
- Members dialog: `show_members_dialog`, `members_tenant_id`, `members_tenant_name`
- Delete dialog: `show_delete_dialog`, `deleting_tenant_id`, `deleting_tenant_name`
- Messages: `success_message`, `error`, `is_loading`

**Computed vars:**
- `active_count`, `inactive_count`, `total_count`

**Methods:**
- `load_tenants()` — fetch with filter
- `open_create_dialog()`, `open_edit_dialog(id)`, `close_form_dialog()`
- `save_tenant()` — create or update
- `open_delete_dialog(id)`, `confirm_delete()` — deactivate
- `open_members_dialog(id)` — load tenant users + all users
- `add_member(user_id)` — add user to tenant
- `remove_member(user_id)` — remove user from tenant
- `change_member_role(user_id, role)` — change TenantRole
- Auto-generate slug from name: `set_form_name()` genereert slug

## Stap 5: Tenants Page

`frontend/ims/pages/tenants.py` — zelfde structuur als users.py:

**Layout:**
1. Access guard: `AuthState.is_superuser` (niet `is_admin`)
2. Success/error callouts
3. Stat cards: Totaal / Actief / Inactief
4. Filter bar + "Nieuwe organisatie" knop
5. Desktop tabel: Naam, Slug, Contact, Leden, Status, Acties
6. Mobile cards
7. Dialogen: form, members, delete

**Tabel-acties per tenant (icon buttons):**
- Users-icoon → leden-dialoog (users beheren, TenantRole toekennen)
- Pencil-icoon → bewerken
- User-X-icoon (oranje) → deactiveren

**Leden-dialoog (het belangrijkste):**
- Lijst van huidige leden met naam, email, TenantRole badge, verwijder-knop
- TenantRole wijzigen via select (OWNER/ADMIN/MEMBER)
- "Lid toevoegen" sectie: user-select dropdown + toevoegen-knop

## Stap 6: Sidebar link

`frontend/ims/components/layout.py` — in de BEHEER sectie:

```python
rx.cond(
    AuthState.is_superuser,
    link_fn("Organisaties", "/tenants", "building"),
),
```

Plaatsing: onder "Gebruikers", boven "Beheer". Alleen zichtbaar voor superusers.

## Stap 7: App registratie

`frontend/ims/ims.py`:
- Import `tenants_page` en `TenantState`
- `app.add_page(tenants_page, route="/tenants", title="Organisaties - IMS")`

---

## Verificatie

1. Login als superuser → "Organisaties" verschijnt in sidebar
2. Login als Beheerder (niet-superuser) → "Organisaties" verschijnt NIET
3. Pagina toont alle tenants met user-count
4. Create: vul naam in → slug auto-generated → save → verschijnt in tabel
5. Edit: wijzig naam → save → bijgewerkt
6. Deactiveer: oranje knop → bevestiging → status wordt inactief
7. Leden-dialoog: voeg user toe → verschijnt in lijst → wijzig role naar ADMIN → badge update → verwijder user → verdwijnt
