from app.core.config import get_settings


def init_telemetry() -> None:
    settings = get_settings()
    if not settings.OTEL_SDK_ENABLED:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(
                endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True
            )
            provider.add_span_processor(BatchSpanProcessor(exporter))
    except Exception:
        pass


def instrument_app(app) -> None:
    settings = get_settings()
    if not settings.OTEL_SDK_ENABLED:
        return
    try:
        import opentelemetry.instrumentation.fastapi as _otel_fastapi
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from starlette.routing import Match, Route

        # TODO: HACK upstream bug in opentelemetry-instrumentation-fastapi 0.63b1:
        # _get_route_details line 495 accesses starlette_route.path on a Match.PARTIAL
        # branch without a try/except, crashing on _IncludedRouter objects (e.g. OPTIONS
        # CORS preflight). The FULL-match branch (line 488) already has the guard.
        # Fixed upstream in a later release. Remove this patch once the package is updated.
        def _patched_get_route_details(scope):
            app_ = scope["app"]
            route = None
            for starlette_route in app_.routes:
                match, _ = (
                    Route.matches(starlette_route, scope)
                    if isinstance(starlette_route, Route)
                    else starlette_route.matches(scope)
                )
                if match == Match.FULL:
                    try:
                        route = starlette_route.path
                    except AttributeError:
                        route = scope.get("path")
                    break
                if match == Match.PARTIAL:
                    try:
                        route = starlette_route.path
                    except AttributeError:
                        route = scope.get("path")
            return route

        _otel_fastapi._get_route_details = _patched_get_route_details

        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass
