"""
Entrypoint mínimo del worker de background jobs.

RESERVADO para ADR-003: la tecnología real de la cola (asyncio propio / Celery / ARQ)
se decidirá al construir el módulo de comunicaciones (change C-XX).

Este placeholder permite que docker-compose levante el servicio worker sin lógica real.
"""


async def run_worker():
    while True:
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_worker())
