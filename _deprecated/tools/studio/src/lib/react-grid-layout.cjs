// Local wrapper for react-grid-layout - using .cjs extension for CommonJS handling
const RGL = require('react-grid-layout');

module.exports = {
    Responsive: RGL.Responsive,
    WidthProvider: RGL.WidthProvider,
    default: RGL
};
