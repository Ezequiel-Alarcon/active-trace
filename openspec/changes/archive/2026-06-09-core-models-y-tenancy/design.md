## Context

`C-01 foundation-setup` dejó el esqueleto FastAPI + SQLAlchemy async + Alembic configurado y conexión a PostgreSQL operativa. Sin embargo, el modelo de datos sigue vacío: no existe el `Tenant` raíz, no hay convención de multi-tenancy, no hay cifrado en reposo disponible, y no hay un repository base. C-02 es el cimiento del aislamiento multi-tenant, del cifrado de PII y del soft delete — todo lo demás (C-03 a C-24) se construye encima de estas primitivas. La decisión arquitectónica ya está tomada en `docs/ARQUITECTURA.md` §6 y §8 (ADR-002 row-level + AES-256 para PII + soft delete); este change codifica esa decisión, no la debate.

**Restricciones duras del proyecto (heredadas de AGENTS.md):**

- Identidad SIEMPRE desde JWT (regla 8) — el helper de tenant se diseña para ser alimentado por el resolver de C-03, no por parámetros de request.
- Multi-tenancy row-level (regla 9) — repositories filtran por `tenant_id` por defecto; un query sin scope es un bug.
- PII cifrada AES-256 (regla 12) — nada en texto plano, nunca en logs.
- Soft delete siempre (regla 13) — append-only, sin hard delete.
- Identidad por UUID interno (regla 14) — `id` = `UUID`, no integer ni legajo.
- ≤500 LOC por archivo backend, snake_case en Python, `extra='forbid'` en Pydantic.

## Goals / Non-Goals

**Goals:**

- Fijar el `Tenant` como raíz inmutable de toda identidad de datos.
- Hacer que escribir un query que cruce tenants sea **imposible por construcción**: el repository base no expone un método que omita el scope de tenant, y los métodos que sí lo hacen están marcados con sufijo `_unsafe_`.
- Garantizar que toda entidad nueva lleva por defecto `id` UUID, `tenant_id`, `created_at`, `updated_at`, `deleted_at`, con índices correctos.
- Proveer cifrado AES-256-GCM listo para que `Usuario` (C-07) cifre email/DNI/CUIL/CBU/alias_cbu sin reinventarlo.
- Dejar la tubería Alembic operativa y con una primera migración reversible.
- Cubrir con tests los invariantes críticos: aislamiento, soft delete, cifrado round-trip, AAD por tenant.

**Non-Goals (explícitos):**

- No se implementa auth, JWT, ni login (eso es C-03).
- No se implementa RBAC ni matriz de permisos (C-04).
- No se implementa `AuditLog` (C-05), aunque el seam queda previsto en el repository base.
- No se crea ninguna entidad de dominio académico (Carrera, Cohorte, Materia, Usuario, etc.); el cimiento se valida con un único modelo de smoke (`Tenant`) más un modelo de prueba interno del repository base (no persistido en producción).
- No se decide todavía el worker de cola (ADR-003) ni la estrategia de impersonación (ADR-004).
- No se modifica el stack de C-01 (sigue FastAPI + SQLAlchemy 2.0 async + Alembic + Pydantic v2 + PostgreSQL).
- No se introduce un ORM distinto, ni DB-per-tenant, ni cifrado por aplicación externa (envelope encryption con KMS queda fuera de scope MVP).

## Decisions

### D1. Aislamiento por construcción: `TenantScopedRepository` como punto único de queries

**Decisión**: Toda query SQLAlchemy del proyecto pasa por un repository que hereda de `TenantScopedRepository[T]`. No existe un "session.query(Model)" suelto en services ni routers.

**Por qué**: La regla 9 ("un query sin scope de tenant es un bug") solo se puede enforced por construcción si el repository base es el único path. Si los services pueden tocar la sesión directamente, el filtro se olvida en el primer PR con presión de tiempo.

**Cómo se enforce**:

- `TenantScopedRepository.__init__(self, session: AsyncSession, tenant_id: UUID)` exige el tenant explícitamente.
- Cada método público (`get`, `list`, `create`, `update`, `soft_delete`, `restore`, `count`) filtra por `tenant_id` y `deleted_at IS NULL` en la query.
- Los métodos que cruzan tenant (admin cross-tenant, scripts de mantenimiento) tienen prefijo `unsafe_` (`unsafe_list_all`, `unsafe_get`, `unsafe_count`) y dejan un `audit_emit(...)` como seam que C-05 cableará al sink real.
- `services/` solo recibe repos tipados (no la sesión cruda) vía una factory `get_tenant_repository(model)` resuelta en el dependency de FastAPI. La sesión cruda se inyecta únicamente a repos y a Alembic.

**Alternativas consideradas**:

- *Hook de SQLAlchemy event* (`before_compile`) que inyecta `tenant_id` automáticamente: probado, pero no funciona bien con queries que legítimamente deben cruzar tenant (jobs admin). Descartado por la propia necesidad de excepción.
- *Row-Level Security de PostgreSQL* (políticas RLS con `SET app.current_tenant`): buena defensa en profundidad, pero la decisión es **defensa en profundidad opcional en Fase 2+**; en MVP C-02 se apoya en la convención del repository, y se documenta el path para sumar RLS en una migración futura. El motivo: RLS agrega fricción operacional (sesión por request, superuser bypass para migraciones) que queremos pagar solo cuando el segundo tenant entre en producción.

### D2. Mixin `TenantScopedMixin` con UUID PK y `tenant_id` NOT NULL FK

**Decisión**: Todo modelo de dominio hereda de un único mixin que aporta `id` (UUID PK, default `uuid4`), `tenant_id` (UUID, NOT NULL, FK a `tenant.id` ON DELETE RESTRICT), `created_at`, `updated_at`, `deleted_at`.

**Por qué**:

- UUID PK (regla 14) garantiza que el legajo nunca pueda colarse como identidad.
- `tenant_id` NOT NULL con FK a `tenant` hace que un INSERT sin tenant falle a nivel DB, no solo a nivel app.
- ON DELETE RESTRICT impide borrar un tenant con datos colgados (operación debe ser explícita y soft).
- Centralizar el mixin evita divergencia entre modelos.

**Cómo se modela**:

```python
class TenantScopedMixin:
    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    __table_args__ = (
        Index("ix_<tabla>_tenant", "tenant_id"),
        Index("ix_<tabla>_tenant_deleted", "tenant_id", "deleted_at"),
    )
```

**Alternativas consideradas**:

- *PK compuesta `(tenant_id, id)`*: tentador (toda query toca el índice compuesto), pero rompe el patrón ORM estándar y complica los FKs desde otras tablas. Descartado.
- *Partitioning por tenant*: over-engineering para el volumen actual; se documenta como opción Fase 2+ si el dataset por tenant crece mucho.

### D3. Soft delete transversal: `deleted_at` + query helper + `soft_delete()` / `restore()`

**Decisión**: Soft delete es un mixin (`SoftDeleteMixin`) que aporta la columna `deleted_at`, y el repository base ofrece `soft_delete(obj)` y `restore(obj)`. Por defecto, `list`/`get`/`count` filtran `deleted_at IS NULL`. El método `unsafe_list_all` lo ignora.

**Por qué**:

- Regla 13 (soft delete siempre) + regla 15 (auditoría append-only). Borrar físicamente una calificación, una liquidación o un padron destruye la trazabilidad del producto (es *trace*).
- Centralizar el filtro en el repository base garantiza que ninguna pantalla vea registros soft-deleted por accidente.
- `restore()` permite que un admin deshaga una baja sin perder historial.

**Cómo se evita el hard delete**:

- `models.Base` redefine `__delete__` no aplica (SQLAlchemy no respeta eso nativamente); en su lugar, los repositories no exponen `session.delete(...)`. El único punto que llama `delete` a la sesión es un helper `physical_delete()` interno al `BaseRepository` con prefijo `unsafe_` y nota explícita de auditoría.
- Lint rule custom (Ruff `S608` + plugin propio) revisa que no exista `session.delete(` ni `Model.__table__.delete()` en `services/`. Es un check, no un sustituto de revisión humana.

**Alternativas consideradas**:

- *Eventos SQLAlchemy `before_delete` que conviertan a UPDATE*: agrega runtime y oculta la semántica. Descartado.
- *Columna `is_active` boolean*: más simple pero pierde el timestamp de baja (cuándo se borró, por quién, para auditoría). Descartado.

### D4. Cifrado AES-256-GCM con AAD = `tenant_id`

**Decisión**: Helper en `core/security/crypto.py` usa AES-256-GCM (modo autenticado, no CBC). El `additional_data` (AAD) del GCM es el `tenant_id` en bytes; un ciphertext producido para el tenant A no es descifrable por el tenant B aunque comparta la misma `ENCRYPTION_KEY`.

**Por qué**:

- AES-GCM da confidencialidad + integridad (detecta manipulación del ciphertext). CBC exige HMAC separado y es propenso a errores.
- AAD por tenant es la defensa en profundidad frente a bugs que filtren ciphertexts entre tenants (un atacante que robe un blob de la tabla `usuario.email` no puede descifrarlo desde otro tenant, ni siquiera con la clave global).
- IV aleatorio de 96 bits (estándar GCM) por cifrado, almacenado como prefijo del ciphertext (`iv || tag || ciphertext` en base64).

**API**:

```python
def encrypt(plaintext: str, *, tenant_id: UUID, aad_suffix: str | None = None) -> str
def decrypt(ciphertext_b64: str, *, tenant_id: UUID, aad_suffix: str | None = None) -> str
def encrypt_bytes(plaintext: bytes, *, tenant_id: UUID, aad_suffix: str | None = None) -> bytes
def decrypt_bytes(ciphertext: bytes, *, tenant_id: UUID, aad_suffix: str | None = None) -> bytes
```

`aad_suffix` permite encadenar el `column_name` (`"usuario.email"`) para que un ciphertext swap entre columnas (mover un cifrado de `dni` a `cbu`) también falle a nivel GCM. Esto se usa en C-07 cuando se cree el modelo `Usuario`.

**Reglas operacionales**:

- El helper **nunca** loggea plaintext, ciphertext descifrado, ni el AAD en claro cuando incluye PII.
- `Settings.ENCRYPTION_KEY` se valida al startup: exactamente 32 bytes (256 bits), `SecretStr` en Pydantic, fail-fast si no cumple.
- En dev se acepta una clave default de un archivo `.env.dev` ignorado por git; en prod la clave vive en el secret manager (Easypanel).
- Rotación de clave: **fuera de scope MVP**. Se documenta el seam (helper recibe `key_version` para multi-key) pero la primera versión usa una sola clave. Razón: la rotación retroactiva de ciphertexts existentes es un proyecto aparte que C-02 no debe bloquear.

**Alternativas consideradas**:

- *Fernet (cryptography)*: más simple, pero no permite AAD arbitrario. Descartado por perder la atadura a tenant.
- *AES-CBC + HMAC*: más piezas que coordinar, mismo objetivo, más superficie de bug. Descartado.
- *Envelope encryption con KMS*: correcto, fuera de presupuesto MVP. Roadmap Fase 2+.

### D5. `TenantContext` y resolución desde sesión (placeholder hasta C-03)

**Decisión**: `core/tenancy.py` expone `TenantContext` (dataclass con `tenant_id: UUID` y `is_impersonating: bool`) y `get_current_tenant_id()` que lee del `ContextVar` de asyncio. En C-02, `get_current_tenant_id()` **no** se cablea todavía al JWT (eso es C-03); se inicializa vía dependency de FastAPI `set_tenant_context(tenant_id)` que en C-02 solo se usa en tests y en el endpoint `/health` extendido. En C-03 ese dependency se reemplaza por el resolver del JWT verificado.

**Por qué**:

- C-02 fija la forma del contrato (`TenantContext`) sin atarse a un mecanismo de auth que todavía no existe.
- Tests de C-02 pueden setear el `ContextVar` directamente y simular multi-tenant sin necesitar auth.
- En C-03 el cambio es solo el cable, no el contrato — minimiza el refactor.

**Alternativas consideradas**:

- *Pasar `tenant_id` como parámetro explícito en cada llamada al repository*: más explícito, pero hace que el repository reciba un argumento que NUNCA debería variar dentro de un request → acopla toda la API al anti-patrón de "thread-local global". Descartado.
- *Resolver `tenant_id` desde el `Authorization` header en cada query*: viola la regla 8. Descartado.

### D6. Migración Alembic: convención de nombres + template de script

**Decisión**:

- Convención de nombres: prefijo numérico `NNN_descripcion.py` (consecutivo, no timestamps). Razón: legibilidad humana al buscar migraciones en git log.
- `env.py` async (usa `asyncpg`, no psycopg2) con `run_async_migrations()`.
- `script.py.mako` incluye un comentario recordatorio: "Si tu tabla no es de sistema (no es `tenant` ni catálogo global), debe heredar de `TenantScopedMixin` y llevar `tenant_id` + `deleted_at`."
- Convención de nombres SQL (constraints/índices): `ix_<tabla>_<col>`, `uq_<tabla>_<cols>`, `fk_<tabla>_<cols>`, `ck_<tabla>_<col>`, `pk_<tabla>`. Aplicada vía `op.create_index(..., postgresql_concurrently=False)`.
- Reversibilidad: cada migración implementa `downgrade()` real (no `pass`). El seed de tenant inicial se hace en una migración de datos aparte (`002_seed_dev_tenant.py`, fuera de scope de C-02 — el seed de dev se hace por fixture en tests).

**Por qué**:

- El camino crítico (24 changes) va a acumular muchas migraciones. La convención tiene que ser legible y aplicar sola.
- Reversibilidad obligatoria porque en MVP los tenants todavía no están en producción y se itera seguido; más adelante, las migraciones con efectos irreversibles se marcan con `REVIEW_REQUIRED` en el docstring.

**Alternativas consideradas**:

- *Alembic con timestamps en lugar de numerales*: convención de la herramienta, pero los diffs en git log se ordenan mal cuando se mergean dos features en paralelo. Descartado a favor de numerales.
- *Una migración por change*: implícito en la regla 15 ("una migración Alembic por cambio de schema") — no es una alternativa, es la regla.

### D7. Política de tests: DB real, nunca mock

**Decisión** (ya fijada en AGENTS.md, se re-confirma acá): los tests de C-02 usan una base PostgreSQL real (contenedor `postgres:16` levantado en pytest fixture). Prohibido `unittest.mock` sobre `AsyncSession` o `TenantScopedRepository`.

**Por qué**: C-02 es cimiento de aislamiento. Un test con mock que sustituye el repository no prueba nada: si el código se equivoca de filtro, el mock también lo acepta. La única manera de probar "tenant A no lee datos de tenant B" es contra una DB real con dos tenants sembrados.

**Cómo se ejecuta**:

- `conftest.py` levanta un contenedor `postgres:16` con `testcontainers-python` (o `docker run` directo) una vez por sesión de pytest.
- Cada test corre dentro de una transacción que se rollback-ea al final (`SAVEPOINT`-style), salvo los tests de migración que aplican y revierten Alembic explícitamente.
- Cifrado se testea con la misma `ENCRYPTION_KEY` que producción (viene de env var de test, no hardcodeada).
- Cobertura objetivo: ≥80% líneas; las reglas de soft delete, cifrado y aislamiento multi-tenant persiguen ≥90% (regla de negocio).

## Risks / Trade-offs

- **R1 — Falsa sensación de seguridad con AAD**: el AAD por tenant es defensa en profundidad, no sustituto del filtro del repository. Si en algún módulo futuro un developer bypassea el repository y arma una query cruda, el AAD no lo salva. *Mitigación*: lint rule + code review checklist (ver D1). *Riesgo residual*: bajo mientras el equipo revise; alto si crece sin disciplina.

- **R2 — Soft delete puede acumular basura**: como nunca se borra físicamente, la tabla crece para siempre. *Mitigación*: se documenta la política de particionado/archivado en `docs/ARQUITECTURA.md` (futuro). En MVP, el volumen esperado no lo amerita. *Trigger de revisión*: si alguna tabla supera 10M filas antes de Fase 2.

- **R3 — Cifrado en logs accidental**: si un developer loggea `obj.email` y `email` es un `EncryptedString` (tipo Pydantic custom) que descifra en `__str__`, se filtra. *Mitigación*: el tipo `EncryptedString` (C-07) tendrá `__repr__ = __str__ = lambda self: "***"`; C-02 deja el seam (helper `EncryptedField` para Pydantic) pero el modelo `Usuario` es C-07. Igual, Ruff rule custom revisa `logger.info(f"...{obj.email}"`.

- **R4 — `ENCRYPTION_KEY` en `.env` accidentalmente commiteada**: el `.env.dev` local es tentación. *Mitigación*: `.gitignore` ignora `.env*` salvo `.env.example`; pre-commit hook con `detect-secrets` corre `git secrets --scan` en CI. Ya provisto en C-01; C-02 valida que la regla siga activa.

- **R5 — Alembic async + `asyncio` del lado Alembic + concurrencia con tests**: race conditions en `Base.metadata` entre sesiones paralelas. *Mitigación*: cada test usa su propia `AsyncSession` con `expire_on_commit=False`; las migraciones se aplican en `None` (sin sesión abierta). *Riesgo residual*: solo impacta a quien escriba migraciones concurrentes en mismo proceso.

- **R6 — Repository base como god object**: tentación de meter lógica de negocio ahí. *Mitigación*: el `TenantScopedRepository` solo tiene CRUD + soft delete + restore. Lógica de dominio va en `services/` (regla 11). Code review rejecta PRs con `.list(filter=X, order_by=Y, aggregate=Z)` complejo en el base; eso va en repos específicos.

- **R7 — Cambio del contrato `TenantContext` entre C-02 y C-03**: si C-03 necesita un campo más (por ej. `is_impersonating`, que ya está previsto), el cambio es compatible hacia atrás (campo default). Si C-03 necesita remover un campo, hay refactor. *Mitigación*: en C-02 se incluyen los campos mínimos más `is_impersonating: bool` (default False) como placeholder. C-03 lo usa tal cual.

## Migration Plan

C-02 es netamente aditivo sobre C-01, por lo que no hay plan de rollback de datos en producción. Plan de despliegue:

1. **Aplicar migración 001** (en orden, contra DB de staging primero):
   - `alembic upgrade head` desde `backend/`. Crea tabla `tenant`.
2. **No hay código de aplicación que la use todavía**: el endpoint que crea tenants llega con un módulo de admin en C-21+ o con un seed manual. En este change, el tenant de smoke se crea por test/fixture.
3. **Verificación post-deploy**:
   - `SELECT count(*) FROM tenant;` debe ser 0 (vacía) o N (si el seed se ejecutó).
   - `psql \d tenant` debe mostrar columnas: `id`, `codigo`, `nombre`, `estado`, `created_at`, `updated_at`, `deleted_at`, con índice único en `codigo` (cuando se cree) y check en `estado`.
4. **Rollback**: `alembic downgrade -1` revierte la migración 001. No hay pérdida de datos porque la tabla queda vacía en este punto del roadmap.
5. **Próximos steps**: C-03 introduce `Usuario` que FKea a `tenant.id` y FKea a `tenant.id` el modelo `AuditLog` en C-05. El seed del primer tenant de desarrollo se hace por fixture pytest y por un script `seed_dev.py` que llega con C-03.

## Open Questions

- **OQ-1**: ¿La tabla `tenant` necesita un campo `configuracion` JSONB para el setting per-tenant (idioma, branding, flag de aprobación de mails, plantillas) que ya menciona la KB? **Decisión propuesta**: **no en C-02**, se difiere a un change dedicado `C-XX tenant-config` cuando aparezca el primer endpoint que lo lea. Razón: YAGNI; meter JSONB ahora sin consumidor lo convierte en deuda. ¿Confirmás diferirlo? Si decís que sí, queda como TASK explícito en tasks.md.

- **OQ-2**: ¿La columna `tenant.codigo` debe ser única global o única por `deleted_at IS NULL` (parcial)? **Decisión propuesta**: única global. Si se hace soft delete de un tenant, su `codigo` no se libera — un tenant dado de baja no debería renacer con el mismo código. Si preferís unique parcial para permitir re-uso tras baja, es un cambio de una línea, pero el comportamiento operativo difiere. ¿Cuál preferís?

- **OQ-3**: ¿Necesitamos una tabla `tenant` separada del usuario, o la raíz multi-tenant puede vivir como columna en una tabla `configuracion` global? **Decisión propuesta**: tabla propia (decisión ya implícita en la KB y en la arquitectura). Lo dejo escrito igual por las dudas.

- **OQ-4**: ¿Conviene crear un modelo "dummy" adicional al `Tenant` para validar que el mixin funciona end-to-end, o basta con tests unitarios del mixin + tests de integración contra `Tenant`? **Decisión propuesta**: tests unitarios del mixin + tests de integración contra `Tenant` con un modelo interno de prueba `Smoke` (no persistido) en `tests/_fakes/`. Razón: introduce un modelo de dominio real (ej. `Materia`) que no corresponde a C-02. ¿OK?

- **OQ-5**: ¿El helper de cifrado admite un `key_id` (key_version) ya desde MVP para no romper la rotación futura, o lo dejamos out? **Decisión propuesta**: incluir `key_id: int = 1` ya en la firma del helper, aunque la `Settings` solo cargue una clave. Razón: una vez que hay ciphertexts en producción, agregar `key_id` retroactivamente es costoso (hay que re-cifrar o inferir). Mejor incluirlo desde el día 0 y no usarlo hasta que la rotación aparezca. ¿OK?
