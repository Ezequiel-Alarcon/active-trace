"""Strict TDD for Usuario model + PII encryption (C-07 §7).

Tests cover:
- PII fields encrypted at rest (email_enc != plaintext)
- Round-trip encrypt -> decrypt
- email_hash determinism
- Uniqueness: same email + tenant -> error, diff tenant -> OK
- PII NEVER in __repr__
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security.crypto import CryptoError, decrypt, encrypt
from app.core.security.hashing import hash_email_for_search
from app.models.base import Base
from app.models.usuario import Usuario
from app.repositories.usuarios import (
    _AAD_CBU,
    _AAD_DNI,
    _AAD_EMAIL,
    decrypt_usuario_fields,
    encrypt_usuario_fields,
)

pytestmark = pytest.mark.no_db

TENANT_A = uuid4()
TENANT_B = uuid4()


# ── 7.1 PII Encryption ───────────────────────────────────────────────

def test_email_enc_different_from_plaintext() -> None:
    data = encrypt_usuario_fields(
        {"email": "maria@garcia.com", "dni": "20123456", "cuil": "20-20123456-9", "cbu": "2850590940090418135201"},
        tenant_id=TENANT_A,
    )
    assert "email" not in data
    assert "email_enc" in data
    assert "email_hash" in data
    assert data["email_enc"] != "maria@garcia.com"


def test_all_pii_fields_encrypted() -> None:
    data = encrypt_usuario_fields(
        {
            "email": "test@test.com",
            "dni": "12345678",
            "cuil": "20-12345678-9",
            "cbu": "1234567890123456789012",
            "alias_cbu": "test.alias.cbu",
        },
        tenant_id=TENANT_A,
    )
    assert "email" not in data
    assert "dni" not in data
    assert "cuil" not in data
    assert "cbu" not in data
    assert "alias_cbu" not in data
    assert "email_enc" in data
    assert "dni_enc" in data
    assert "cuil_enc" in data
    assert "cbu_enc" in data
    assert "alias_cbu_enc" in data
    assert data["email_enc"] != "test@test.com"
    assert data["dni_enc"] != "12345678"


def test_non_pii_fields_remain_plaintext() -> None:
    data = encrypt_usuario_fields(
        {"nombre": "María", "apellidos": "García", "legajo": "L-1234", "email": "m@test.com", "dni": "123", "cuil": "123", "cbu": "123"},
        tenant_id=TENANT_A,
    )
    assert data["nombre"] == "María"
    assert data["apellidos"] == "García"
    assert data["legajo"] == "L-1234"


def test_round_trip_email_decrypts_correctly() -> None:
    plain = "roundtrip@test.com"
    data = encrypt_usuario_fields({"email": plain, "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="X", apellidos="Y", **data)
    fields = decrypt_usuario_fields(u)
    assert fields["email"] == plain


def test_round_trip_dni_decrypts_correctly() -> None:
    plain = "40123456"
    data = encrypt_usuario_fields({"email": "x@x.com", "dni": plain, "cuil": "2", "cbu": "3"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="X", apellidos="Y", **data)
    fields = decrypt_usuario_fields(u)
    assert fields["dni"] == plain


def test_round_trip_cuil_decrypts_correctly() -> None:
    plain = "20-40123456-9"
    data = encrypt_usuario_fields({"email": "x@x.com", "dni": "1", "cuil": plain, "cbu": "3"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="X", apellidos="Y", **data)
    fields = decrypt_usuario_fields(u)
    assert fields["cuil"] == plain


def test_round_trip_cbu_decrypts_correctly() -> None:
    plain = "2850590940090418135201"
    data = encrypt_usuario_fields({"email": "x@x.com", "dni": "1", "cuil": "2", "cbu": plain}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="X", apellidos="Y", **data)
    fields = decrypt_usuario_fields(u)
    assert fields["cbu"] == plain


def test_round_trip_alias_cbu_decrypts_correctly() -> None:
    plain = "mi.alias.cbu.test"
    data = encrypt_usuario_fields(
        {"email": "x@x.com", "dni": "1", "cuil": "2", "cbu": "3", "alias_cbu": plain}, tenant_id=TENANT_A
    )
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="X", apellidos="Y", **data)
    fields = decrypt_usuario_fields(u)
    assert fields["alias_cbu"] == plain


def test_alias_cbu_null_not_encrypted() -> None:
    data = encrypt_usuario_fields(
        {"email": "x@x.com", "dni": "1", "cuil": "2", "cbu": "3", "alias_cbu": None}, tenant_id=TENANT_A
    )
    assert "alias_cbu_enc" not in data


def test_alias_cbu_none_value_persisted_as_null() -> None:
    data = encrypt_usuario_fields(
        {"email": "x@x.com", "dni": "1", "cuil": "2", "cbu": "3", "alias_cbu": "some.alias"}, tenant_id=TENANT_A
    )
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="X", apellidos="Y",
                email_hash=data["email_hash"], email_enc=data["email_enc"],
                dni_enc=data["dni_enc"], cuil_enc=data["cuil_enc"],
                cbu_enc=data["cbu_enc"], alias_cbu_enc=None)
    fields = decrypt_usuario_fields(u)
    assert "alias_cbu" not in fields


# ── email_hash determinism ────────────────────────────────────────────

def test_email_hash_is_deterministic() -> None:
    a = hash_email_for_search("user@test.com", TENANT_A)
    b = hash_email_for_search("user@test.com", TENANT_A)
    assert a == b


def test_email_hash_differs_by_tenant() -> None:
    a = hash_email_for_search("user@test.com", TENANT_A)
    b = hash_email_for_search("user@test.com", TENANT_B)
    assert a != b


def test_email_hash_depends_on_exact_input() -> None:
    a = hash_email_for_search("user@test.com", TENANT_A)
    b = hash_email_for_search("user@test.com", TENANT_A)
    assert a == b


def test_encrypt_usuario_fields_lowercases_email_before_hashing() -> None:
    data = encrypt_usuario_fields(
        {"email": "User@Test.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=TENANT_A
    )
    expected = hash_email_for_search("user@test.com", TENANT_A)
    assert data["email_hash"] == expected


def test_email_hash_stored_in_encrypted_fields() -> None:
    data = encrypt_usuario_fields({"email": "hash@test.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=TENANT_A)
    expected = hash_email_for_search("hash@test.com", TENANT_A)
    assert data["email_hash"] == expected


# ── 7.3 __repr__ NEVER leaks PII ─────────────────────────────────────

def test_repr_does_not_contain_email() -> None:
    data = encrypt_usuario_fields({"email": "secret@email.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="Ana", apellidos="Lopez", **data)
    r = repr(u)
    assert "secret@email.com" not in r
    assert "email" not in r.lower()


def test_repr_does_not_contain_dni() -> None:
    data = encrypt_usuario_fields({"email": "x@x.com", "dni": "40123456", "cuil": "2", "cbu": "3"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="Ana", apellidos="Lopez", **data)
    r = repr(u)
    assert "40123456" not in r


def test_repr_does_not_contain_cuil() -> None:
    data = encrypt_usuario_fields({"email": "x@x.com", "dni": "1", "cuil": "20-40123456-9", "cbu": "3"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="Ana", apellidos="Lopez", **data)
    r = repr(u)
    assert "40123456" not in r


def test_repr_does_not_contain_cbu() -> None:
    data = encrypt_usuario_fields({"email": "x@x.com", "dni": "1", "cuil": "2", "cbu": "2850590940090418135201"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="Ana", apellidos="Lopez", **data)
    r = repr(u)
    assert "2850590940090418135201" not in r


def test_repr_does_not_contain_ciphertext() -> None:
    data = encrypt_usuario_fields({"email": "x@x.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="Ana", apellidos="Lopez", **data)
    r = repr(u)
    assert data["email_enc"] not in r
    assert data["dni_enc"] not in r
    assert data["cuil_enc"] not in r
    assert data["cbu_enc"] not in r


def test_repr_only_shows_non_pii_fields() -> None:
    data = encrypt_usuario_fields({"email": "x@x.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=TENANT_A)
    uid = uuid4()
    u = Usuario(id=uid, tenant_id=TENANT_A, nombre="Ana", apellidos="Lopez", **data)
    r = repr(u)
    assert "Ana" in r
    assert "Lopez" in r
    assert str(uid) in r
    assert "Usuario" in r


# ── AAD enforcement (cross-field) ─────────────────────────────────────

def test_ciphertext_of_email_not_decryptable_as_dni() -> None:
    cipher = encrypt("maria@garcia.com", tenant_id=TENANT_A, aad_suffix=_AAD_EMAIL)
    with pytest.raises(CryptoError):
        decrypt(cipher, tenant_id=TENANT_A, aad_suffix=_AAD_DNI)


def test_ciphertext_of_dni_not_decryptable_as_cbu() -> None:
    cipher = encrypt("40123456", tenant_id=TENANT_A, aad_suffix=_AAD_DNI)
    with pytest.raises(CryptoError):
        decrypt(cipher, tenant_id=TENANT_A, aad_suffix=_AAD_CBU)


def test_ciphertext_cross_tenant_fails() -> None:
    cipher = encrypt("40123456", tenant_id=TENANT_A, aad_suffix=_AAD_DNI)
    with pytest.raises(CryptoError):
        decrypt(cipher, tenant_id=TENANT_B, aad_suffix=_AAD_DNI)


# ── 7.1 Uniqueness (DB-backed) ────────────────────────────────────────

@pytest_asyncio.fixture
async def db_setup():
    from app.models import tenant  # noqa: F401
    from app.models import usuario  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        # TODO: (HACK) SQL raw con CASCADE en lugar de Base.metadata.drop_all() — ver
        # backend/tests/calificaciones/conftest.py para explicación completa.
        await conn.execute(sqlalchemy.text("""
            DO $$ DECLARE r RECORD; BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_unique_email_same_tenant_rejected(db_setup) -> None:
    from app.models.tenant import Tenant, TenantEstado

    async with db_setup() as session:
        t = Tenant(codigo="UNIQ", nombre="Uniq Test", estado=TenantEstado.ACTIVO)
        session.add(t)
        await session.flush()
        tid = t.id

        enc = encrypt_usuario_fields(
            {"email": "dup@test.com", "dni": "11111111", "cuil": "20-11111111-9", "cbu": "1111111111111111111111"},
            tenant_id=tid,
        )
        u1 = Usuario(id=uuid4(), tenant_id=tid, nombre="A", apellidos="B", **enc)
        session.add(u1)
        await session.flush()

        enc2 = encrypt_usuario_fields(
            {"email": "dup@test.com", "dni": "22222222", "cuil": "20-22222222-9", "cbu": "2222222222222222222222"},
            tenant_id=tid,
        )
        u2 = Usuario(id=uuid4(), tenant_id=tid, nombre="C", apellidos="D", **enc2)
        session.add(u2)
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await session.flush()


@pytest.mark.asyncio
async def test_same_email_different_tenant_allowed(db_setup) -> None:
    from app.models.tenant import Tenant, TenantEstado

    async with db_setup() as session:
        t_a = Tenant(codigo="TA", nombre="Tenant A", estado=TenantEstado.ACTIVO)
        t_b = Tenant(codigo="TB", nombre="Tenant B", estado=TenantEstado.ACTIVO)
        session.add_all([t_a, t_b])
        await session.flush()
        tid_a = t_a.id
        tid_b = t_b.id

        enc_a = encrypt_usuario_fields(
            {"email": "shared@test.com", "dni": "11111111", "cuil": "20-11111111-9", "cbu": "1111111111111111111111"},
            tenant_id=tid_a,
        )
        u_a = Usuario(id=uuid4(), tenant_id=tid_a, nombre="A", apellidos="B", **enc_a)
        session.add(u_a)
        await session.flush()

        enc_b = encrypt_usuario_fields(
            {"email": "shared@test.com", "dni": "22222222", "cuil": "20-22222222-9", "cbu": "2222222222222222222222"},
            tenant_id=tid_b,
        )
        u_b = Usuario(id=uuid4(), tenant_id=tid_b, nombre="C", apellidos="D", **enc_b)
        session.add(u_b)
        await session.flush()

        assert u_a.id != u_b.id


@pytest.mark.asyncio
async def test_email_hash_differs_between_tenants(db_setup) -> None:
    from app.models.tenant import Tenant, TenantEstado

    async with db_setup() as session:
        t_a = Tenant(codigo="TA2", nombre="Tenant A2", estado=TenantEstado.ACTIVO)
        t_b = Tenant(codigo="TB2", nombre="Tenant B2", estado=TenantEstado.ACTIVO)
        session.add_all([t_a, t_b])
        await session.flush()
        tid_a = t_a.id
        tid_b = t_b.id

        enc_a = encrypt_usuario_fields(
            {"email": "same@test.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=tid_a
        )
        enc_b = encrypt_usuario_fields(
            {"email": "same@test.com", "dni": "1", "cuil": "2", "cbu": "3"}, tenant_id=tid_b
        )
        assert enc_a["email_hash"] != enc_b["email_hash"]
