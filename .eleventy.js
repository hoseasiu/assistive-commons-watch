module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy({ "site/assets": "assets" });

  // Make tier color available in templates
  eleventyConfig.addFilter("tierColor", (tier) => {
    const colors = {
      thriving: "oklch(0.52 0.16 142)",
      stable: "oklch(0.50 0.14 245)",
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
      dormant: "Dormant",
      at_risk: "At Risk",
      archived: "Archived",
      unverified: "Unverified",
    };
    return labels[tier] ?? tier;
  });

  return {
    dir: {
      input: "site",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
  };
};
