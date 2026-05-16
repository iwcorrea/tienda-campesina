/**
 * Feature flag global. Con true, todas las pantallas v2 se muestran por defecto.
 * El SafeV2Wrapper usará este flag como interruptor principal.
 */
export const FEATURE_V2_PANTALLAS = import.meta.env.VITE_FEATURE_V2_PANTALLAS === 'true';