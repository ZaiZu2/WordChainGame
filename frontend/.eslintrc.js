module.exports = {
    rules: {
        "simple-import-sort/exports": "error",
        "simple-import-sort/imports": "error",
        "unused-imports/no-unused-imports": "error",
        "unused-imports/no-unused-vars": "off",
    },
    plugins: ["simple-import-sort", "unused-imports", "prettier"],
};
