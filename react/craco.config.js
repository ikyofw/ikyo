// craco.config.js
module.exports = {
  webpack: {
    configure: (config) => {
      // allow extension-less ESM imports in node_modules (fix @mui/* fully-specified)
      config.module.rules.push({
        test: /\.m?js$/,
        resolve: { fullySpecified: false },
      });
      return config;
    },
  },
};
