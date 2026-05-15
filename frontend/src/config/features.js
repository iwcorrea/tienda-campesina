/**
 * Feature flags para migración v2.
 * - FEATURE_V2_PANTALLAS: flag global de compilación (master switch).
 * - isV2EnabledForUser(user): flag por usuario basado en el campo features.v2_enabled.
 */

export const FEATURE_V2_PANTALLAS =
  import.meta.env.VITE_FEATURE_V2_PANTALLAS === 'true';

/**
 * Retorna true si el usuario tiene acceso a las pantallas v2.
 * @param {object|null} user - Objeto del usuario desde el contexto de auth.
 */
export function isV2EnabledForUser(user) {
  if (FEATURE_V2_PANTALLAS) return true;
  return user?.features?.v2_enabled === true;
}