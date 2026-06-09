# Repositories — política de queries

**Toda query del proyecto pasa por acá.** No existe un `session.query(...)` ni un `select(...)` en `services/`, `routers/` ni `workers/` que no sea a través de un repositorio.

## Reglas

1. **Servicios y routers reciben repos tipados, jamás la `AsyncSession` cruda.** La factory `get_tenant_repository(model, session)` es la única forma de obtener un repositorio en código de producción (en tests se puede construir `TenantScopedRepository(...)` directamente).
2. **Toda query scopeada filtra por `tenant_id` y por `deleted_at IS NULL`.** Si necesitás un path administrativo cross-tenant o que incluya filas soft-deleted, usá los métodos `unsafe_*` y agregá una nota en la PR justificando por qué el filtro por defecto no sirve.
3. **El hard delete vive solo en `unsafe_physical_delete`.** Cualquier llamada a `session.delete(...)` en otro lugar del código es un bug de review (lint rule + checklist).
4. **Lógica de negocio NO va en el repository base.** El base es CRUD + soft delete + restore. Reglas de dominio (cálculo de atrasados, validaciones de padrón, transiciones de coloquio) van en `services/`.
5. **`unsafe_*` se audita.** Cada llamada emite un evento a través de la seam `audit_emit` (C-02 usa el logger; C-05 cablea al `AuditLog` real).

## Anti-patrones explícitos

```python
# ❌ MAL — query cruda fuera del repository
async def list_active_users(db: AsyncSession, tenant_id: UUID):
    stmt = select(User).where(User.tenant_id == tenant_id, User.deleted_at.is_(None))
    return (await db.execute(stmt)).scalars().all()

# ❌ MAL — session.delete directo
await db.delete(some_obj)

# ❌ MAL — servicio recibe AsyncSession y arma queries
class UserService:
    def __init__(self, db: AsyncSession) -> None: ...

# ✅ BIEN — repositorio factory + métodos del contrato
async def list_active_users(session: AsyncSession) -> list[User]:
    repo = get_tenant_repository(User, session)
    return await repo.list()
```

## Crear un repositorio específico

Si una entidad necesita queries que el base no provee (joins, agregaciones, filtros de dominio), heredá de `TenantScopedRepository[T]` y agregá métodos que **siempre** partan de las columnas del modelo (no aceptar `tenant_id` como parámetro: viene del constructor).

```python
class CalificacionRepository(TenantScopedRepository[Calificacion]):
    async def list_atrasados(self, materia_id: UUID) -> list[Calificacion]:
        stmt = (
            select(Calificacion)
            .where(Calificacion.materia_id == materia_id)
            .where(Calificacion.deleted_at.is_(None))  # nunca olvidar
        )
        return list((await self._session.execute(stmt)).scalars().all())
```

## Por qué esta política

Un query sin scope de tenant es un bug de seguridad, no un descuido estético. El costo de "se me olvidó el filtro" en producción es filtrar datos de un tenant a otro. Hacer cumplir el scope por construcción (el único camino es el repository) es la única manera de que la regla sobreviva al primer PR con presión de tiempo.
