const TELEMETRY_ENDPOINT = '/api/telemetry/pilot';

/**
 * Envía un evento de telemetría de forma asíncrona.
 * No afecta la experiencia de usuario (fire-and-forget).
 */
export function track(event, metadata = {}) {
  const payload = {
    event,
    metadata: {
      ...metadata,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent.substring(0, 100), // limitado
      screenWidth: window.innerWidth,
    },
  };

  // En desarrollo, loguear en consola; en producción, enviar al backend.
  if (import.meta.env.DEV) {
    console.log('[pilot telemetry]', payload);
    return;
  }

  try {
    fetch(TELEMETRY_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      // No esperamos respuesta; simplemente enviamos.
    }).catch(() => {}); 
  } catch {}
}