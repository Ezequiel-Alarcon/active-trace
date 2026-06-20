from __future__ import annotations

from uuid import UUID

from scripts.seed_domain import (
    _MAT_AED,
    _MAT_POO,
    _build_professor_guardias,
    _build_professor_inbox_messages,
)


def test_build_professor_guardias_targets_professor_owned_schedule() -> None:
    profesor_id = UUID("aaaaaaaa-1111-2222-3333-444444444444")

    guardias = _build_professor_guardias(profesor_id)

    assert len(guardias) == 2
    assert {guardia["materia_id"] for guardia in guardias} == {_MAT_AED, _MAT_POO}
    assert {guardia["tutor_id"] for guardia in guardias} == {profesor_id}


def test_build_professor_inbox_messages_creates_two_demo_threads() -> None:
    profesor_id = UUID("aaaaaaaa-1111-2222-3333-444444444444")
    coordinador_id = UUID("bbbbbbbb-1111-2222-3333-444444444444")
    tutor_id = UUID("cccccccc-1111-2222-3333-444444444444")

    mensajes = _build_professor_inbox_messages(profesor_id, coordinador_id, tutor_id)

    assert len(mensajes) == 4
    assert {mensaje["hilo_id"] for mensaje in mensajes}
    assert len({mensaje["hilo_id"] for mensaje in mensajes}) == 2
    assert all(
        profesor_id in {mensaje["remitente_id"], mensaje["destinatario_id"]}
        for mensaje in mensajes
    )
    assert any(
        mensaje["destinatario_id"] == profesor_id and mensaje["leido_at"] is None
        for mensaje in mensajes
    )
