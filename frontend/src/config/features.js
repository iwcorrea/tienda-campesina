/**
 * Feature flags centralizados para la migración v2.
 * En desarrollo, define VITE_FEATURE_V2_PANTALLAS=true en .env.local
 */
export const FEATURE_V2_PANTALLAS =
  import.meta.env.VITE_FEATURE_V2_PANTALLAS === 'true';