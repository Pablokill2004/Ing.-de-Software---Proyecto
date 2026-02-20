import js from "@eslint/js";

export default [
  {
    files: ["**/*.js"],
    languageOptions: {
      sourceType: "module",
    },
  },
  js.configs.recommended,
  {
    rules: {
      complexity: ["warn", 10],
    },
  },
];
