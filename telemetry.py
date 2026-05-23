from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

# Trazas
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(tracer_provider)

# Métricas
reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=10000)
meter_provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(meter_provider)

tracer = trace.get_tracer("dstranslator")
meter = metrics.get_meter("dstranslator")

# Contadores
cache_hits = meter.create_counter("cache_hits", description="Cache hits RAM+SQLite")
cache_misses = meter.create_counter("cache_misses", description="Cache misses")
translations_total = meter.create_counter("translations_total", description="Traducciones completadas")
queue_size = meter.create_up_down_counter("queue_size", description="Textos en cola")