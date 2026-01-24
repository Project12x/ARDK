import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  "stories": [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"
  ],
  "addons": [
    "@chromatic-com/storybook",
    "@storybook/addon-vitest",
    "@storybook/addon-a11y",
    "@storybook/addon-docs",
    "@storybook/addon-onboarding"
  ],
  "framework": "@storybook/react-vite",
  async viteFinal(config) {
    // Filter out vite-plugin-pwa to avoid conflicts with Storybook build
    if (config.plugins) {
      console.log('Plugins before filtering:', config.plugins.map(p => Array.isArray(p) ? p.map(ip => ip ? ip.name : 'unknown') : (p ? p.name : 'unknown')));
      config.plugins = config.plugins.filter((plugin) => {
        // Handle array of plugins (which vite-plugin-pwa often is)
        if (Array.isArray(plugin)) {
          return !plugin.some((p) => p && p.name && p.name.includes('vite-plugin-pwa'));
        }
        // Handle single plugin object
        const p = plugin as any;
        return !(p && p.name && p.name.includes('vite-plugin-pwa'));
      });
      console.log('Plugins after filtering:', config.plugins.map(p => Array.isArray(p) ? p.map(ip => ip ? ip.name : 'unknown') : (p ? p.name : 'unknown')));
    }
    return config;
  }
};
export default config;