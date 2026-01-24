// Local wrapper for react-grid-layout to bypass Vite's ESM resolution issues
// The library uses CommonJS but doesn't properly expose ESM named exports

// @ts-ignore - CommonJS require in ESM context, handled by Vite's CJS interop
// eslint-disable-next-line @typescript-eslint/no-require-imports
const RGL = require('react-grid-layout');

export const Responsive = RGL.Responsive;
export const WidthProvider = RGL.WidthProvider;
export default RGL;
