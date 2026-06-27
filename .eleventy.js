const { EleventyHtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function (eleventyConfig) {
  eleventyConfig.addPlugin(EleventyHtmlBasePlugin);

  eleventyConfig.addPassthroughCopy({ "site/assets": "assets" });

  // Make tier color available in templates
  eleventyConfig.addFilter("tierColor", (tier) => {
    const colors = {
      thriving: "oklch(0.52 0.16 142)",
      stable: "oklch(0.50 0.14 245)",
      complete: "oklch(0.50 0.14 245)",
      dormant: "oklch(0.72 0.13 83)",
      at_risk: "oklch(0.62 0.17 47)",
      archived: "oklch(0.52 0.14 22)",
      unverified: "oklch(0.80 0.02 250)",
    };
    return colors[tier] ?? colors.unverified;
  });

  eleventyConfig.addFilter("tierTextColor", (tier) => {
    const colors = {
      dormant: "oklch(0.30 0.06 80)",
      unverified: "oklch(0.40 0.02 250)",
    };
    return colors[tier] ?? "white";
  });

  eleventyConfig.addFilter("tierLabel", (tier) => {
    const labels = {
      thriving: "Thriving",
      stable: "Stable",
      complete: "Complete",
      dormant: "Dormant",
      at_risk: "At Risk",
      archived: "Archived",
      unverified: "Unverified",
    };
    return labels[tier] ?? tier;
  });

  // Score pill colors — light tinted bg, dark text, WCAG AA compliant
  eleventyConfig.addFilter("scoreBg", (score) => {
    if (score === null || score === undefined) return "oklch(0.93 0.005 75)";
    if (score >= 7) return "oklch(0.92 0.08 142)";
    if (score >= 4) return "oklch(0.96 0.07 83)";
    return "oklch(0.94 0.06 22)";
  });

  eleventyConfig.addFilter("scoreText", (score) => {
    if (score === null || score === undefined) return "oklch(0.44 0.01 75)";
    if (score >= 7) return "oklch(0.28 0.14 142)";
    if (score >= 4) return "oklch(0.40 0.10 83)";
    return "oklch(0.40 0.14 22)";
  });

  eleventyConfig.addFilter("scoreBorder", (score) => {
    if (score === null || score === undefined) return "oklch(0.82 0.01 75)";
    if (score >= 7) return "oklch(0.78 0.12 142)";
    if (score >= 4) return "oklch(0.82 0.10 83)";
    return "oklch(0.80 0.10 22)";
  });

  return {
    pathPrefix: process.env.ELEVENTY_PATH_PREFIX || "/",
    dir: {
      input: "site",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
  };
};
