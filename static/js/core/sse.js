/* =============================================================================
   core/sse.js — No-op stub for cloud web admin.
   ========================================================================== */

export function connect() {
  return null;
}

export function disconnect() {}

export function onMessage() {
  return () => {};
}

export default { connect, disconnect, onMessage };
