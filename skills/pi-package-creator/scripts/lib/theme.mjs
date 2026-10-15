// Embedded contracts from Pi commit b06c1f2cf1dea6af8748ddeee18c23587d2cb7c6: theme-schema.ts, theme-tokens.ts,
// theme.ts resolveVarRefs(), and packages/tui/src/colors.ts.
// This module reads no files, imports no dependencies, and performs no I/O.

const REQUIRED_TOKENS = `
accent border borderAccent borderMuted success error warning muted dim
text thinkingText selectedBg
userMessageBg userMessageText customMessageBg customMessageText customMessageLabel
toolPendingBg toolSuccessBg toolErrorBg toolTitle toolOutput
mdHeading mdLink mdLinkUrl mdCode mdCodeBlock mdCodeBlockBorder
mdQuote mdQuoteBorder mdHr mdListBullet
toolDiffAdded toolDiffRemoved toolDiffContext
syntaxComment syntaxKeyword syntaxFunction syntaxVariable syntaxString
syntaxNumber syntaxType syntaxOperator syntaxPunctuation
thinkingOff thinkingMinimal thinkingLow thinkingMedium thinkingHigh thinkingXhigh
bashMode
`.trim().split(/\s+/);

const OPTIONAL_FALLBACKS = {
  scrollbarTrack: "muted",
  scrollbarThumb: "text",
  searchMatchBg: "selectedBg",
  searchMatchText: "text",
  thinkingMax: "thinkingXhigh",
};

const COLOR_KEYS = new Set([...REQUIRED_TOKENS, ...Object.keys(OPTIONAL_FALLBACKS)]);
const TOP_LEVEL_KEYS = new Set(["$schema", "name", "appearance", "vars", "colors", "export"]);
const EXPORT_KEYS = new Set(["pageBg", "cardBg", "infoBg"]);
// Built-in theme names come first in Pi's theme list, and "system" always resolves to the generated theme.
const RESERVED_THEME_NAMES = new Set(["system", "dark", "light"]);
const HEX_PATTERN = /^#([\da-f]{3}|[\da-f]{6})$/i;
const NUMBER_SOURCE = String.raw`[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?`;
const OKLCH_PATTERN = new RegExp(
  `^oklch\\(\\s*(${NUMBER_SOURCE})(%)?\\s+(${NUMBER_SOURCE})\\s+(${NUMBER_SOURCE})(?:deg)?\\s*\\)$`,
  "i",
);
const OKHSL_PATTERN = new RegExp(
  `^okhsl\\(\\s*(${NUMBER_SOURCE})(?:deg)?\\s+(${NUMBER_SOURCE})(%)?\\s+(${NUMBER_SOURCE})(%)?\\s*\\)$`,
  "i",
);

function isObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function pointer(parent, key) {
  return `${parent}/${String(key).replaceAll("~", "~0").replaceAll("/", "~1")}`;
}

function isColorValue(value) {
  return typeof value === "string"
    || (Number.isInteger(value) && value >= 0 && value <= 255);
}

function validateColorLiteral(value) {
  if (value.startsWith("#")) {
    return HEX_PATTERN.test(value) ? [] : ["Expected a three- or six-digit hexadecimal color"];
  }

  const oklch = OKLCH_PATTERN.exec(value);
  if (oklch) {
    const lightness = Number.parseFloat(oklch[1]) / (oklch[2] ? 100 : 1);
    const chroma = Number.parseFloat(oklch[3]);
    const hue = Number.parseFloat(oklch[4]);
    const errors = [];
    if (!Number.isFinite(lightness) || lightness < 0 || lightness > 1) {
      errors.push("OKLCH lightness must be finite and between 0 and 1, or 0% and 100%");
    }
    if (!Number.isFinite(chroma) || chroma < 0) {
      errors.push("OKLCH chroma must be finite and nonnegative");
    }
    if (!Number.isFinite(hue)) {
      errors.push("OKLCH hue must be finite");
    }
    return errors;
  }

  const okhsl = OKHSL_PATTERN.exec(value);
  if (okhsl) {
    const hue = Number.parseFloat(okhsl[1]);
    const saturation = Number.parseFloat(okhsl[2]) / (okhsl[3] ? 100 : 1);
    const lightness = Number.parseFloat(okhsl[4]) / (okhsl[5] ? 100 : 1);
    const errors = [];
    if (!Number.isFinite(hue)) {
      errors.push("OKHSL hue must be finite");
    }
    if (!Number.isFinite(saturation) || saturation < 0 || saturation > 1) {
      errors.push("OKHSL saturation must be finite and between 0 and 1, or 0% and 100%");
    }
    if (!Number.isFinite(lightness) || lightness < 0 || lightness > 1) {
      errors.push("OKHSL lightness must be finite and between 0 and 1, or 0% and 100%");
    }
    return errors;
  }

  return ["Invalid OKLCH or OKHSL color syntax"];
}

/**
 * Validate a parsed theme JSON value against the embedded baseline contract.
 *
 * The default authoring check also resolves every variable and export color.
 * Pi's normal theme load only resolves variables reachable from `colors`;
 * export colors are resolved separately and their errors may be swallowed.
 * Set checkAllVariables:false to preserve those baseline load semantics.
 *
 * The default check also rejects the built-in names system, dark, and light.
 * Pi's schema accepts them, but a package theme with such a name cannot be
 * selected reliably. Set rejectReservedNames:false to match the schema alone.
 *
 * This checks color syntax and ranges, not color conversion or visual quality.
 * It does not add filename conventions to the JSON contract.
 *
 * @param {unknown} value A parsed JSON value.
 * @param {{checkAllVariables?: boolean, rejectReservedNames?: boolean}} [options]
 * @returns {string[]} Errors prefixed with JSON Pointer locations; empty means valid.
 */
export function validateTheme(value, { checkAllVariables = true, rejectReservedNames = true } = {}) {
  const errors = new Set();
  const report = (location, message) => errors.add(`${location || "/"}: ${message}`);

  if (!isObject(value)) {
    report("", "Expected a theme object");
    return [...errors];
  }

  function checkKeys(object, allowedKeys, location) {
    for (const key of Object.keys(object)) {
      if (!allowedKeys.has(key)) {
        report(pointer(location, key), "Unknown property");
      }
    }
  }

  function checkColorValues(object, location) {
    for (const [key, color] of Object.entries(object)) {
      if (!isColorValue(color)) {
        report(pointer(location, key), "Expected a string or an integer from 0 to 255");
      }
    }
  }

  checkKeys(value, TOP_LEVEL_KEYS, "");
  if (!Object.hasOwn(value, "name")) {
    report("/name", "Required property is missing");
  } else if (typeof value.name !== "string" || value.name.length === 0 || value.name.includes("/")) {
    report("/name", 'Expected a nonempty string without "/"');
  } else if (rejectReservedNames && RESERVED_THEME_NAMES.has(value.name)) {
    report("/name", `Reserved built-in theme name ${JSON.stringify(value.name)}; the built-in theme hides a package theme with this name`);
  }
  if (Object.hasOwn(value, "$schema") && typeof value.$schema !== "string") {
    report("/$schema", "Expected a string");
  }
  if (Object.hasOwn(value, "appearance") && value.appearance !== "dark" && value.appearance !== "light") {
    report("/appearance", 'Expected "dark" or "light"');
  }

  if (Object.hasOwn(value, "vars")) {
    if (!isObject(value.vars)) {
      report("/vars", "Expected an object");
    } else {
      checkColorValues(value.vars, "/vars");
    }
  }
  if (Object.hasOwn(value, "export")) {
    if (!isObject(value.export)) {
      report("/export", "Expected an object");
    } else {
      checkKeys(value.export, EXPORT_KEYS, "/export");
      checkColorValues(value.export, "/export");
    }
  }

  if (!Object.hasOwn(value, "colors")) {
    report("/colors", "Required property is missing");
  } else if (!isObject(value.colors)) {
    report("/colors", "Expected an object");
  } else {
    checkKeys(value.colors, COLOR_KEYS, "/colors");
    for (const token of REQUIRED_TOKENS) {
      if (!Object.hasOwn(value.colors, token)) {
        report(pointer("/colors", token), "Required color token is missing");
      }
    }
    checkColorValues(value.colors, "/colors");
  }

  const variables = isObject(value.vars) ? value.vars : Object.create(null);

  function checkResolvedColor(initialValue, location, initialVariable) {
    let color = initialValue;
    const chain = initialVariable === undefined ? [] : [initialVariable];
    const seen = new Set(chain);

    // Each variable points to one value. An iterative walk handles long chains
    // without recursion and keeps shared references distinct from actual cycles.
    while (isColorValue(color)) {
      if (typeof color === "number" || color === "") return;
      if (color.startsWith("#") || /^ok(lch|hsl)\(/i.test(color)) {
        for (const message of validateColorLiteral(color)) {
          report(location, `${message}: ${JSON.stringify(color)}`);
        }
        return;
      }
      if (seen.has(color)) {
        report(location, `Circular variable reference: ${[...chain, color].map((name) => JSON.stringify(name)).join(" -> ")}`);
        return;
      }
      if (!Object.hasOwn(variables, color)) {
        report(location, `Variable reference not found: ${JSON.stringify(color)}`);
        return;
      }
      seen.add(color);
      chain.push(color);
      color = variables[color];
    }
    // Invalid leaf types already have a schema error at their original path.
  }

  if (isObject(value.colors)) {
    for (const [token, color] of Object.entries(value.colors)) {
      if (COLOR_KEYS.has(token)) {
        checkResolvedColor(color, pointer("/colors", token));
      }
    }
  }

  if (checkAllVariables) {
    for (const [name, color] of Object.entries(variables)) {
      checkResolvedColor(color, pointer("/vars", name), name);
    }
    if (isObject(value.export)) {
      for (const [name, color] of Object.entries(value.export)) {
        if (EXPORT_KEYS.has(name)) {
          checkResolvedColor(color, pointer("/export", name));
        }
      }
    }
  }

  return [...errors];
}
