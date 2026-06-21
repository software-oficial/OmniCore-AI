import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import globals from "globals";

export default [
  js.configs.recommended,
  prettier,
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.serviceworker,
        CONFIG: "readonly",
        PaymentAPI: "readonly",
        LocalDB: "readonly",
        SyncEngine: "readonly",
        StockAPI: "readonly",
        Toast: "readonly",
        WhatsAppAPI: "readonly",
        currentPhone: "readonly",
      },
      ecmaVersion: "latest",
      sourceType: "module",
    },
    rules: {
      "no-unused-vars": "off",
      "no-console": "off",
      "eqeqeq": ["error", "always"],
      "curly": "error",
    },
  },
];
