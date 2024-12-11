local openscad_lsp = require("lspconfig.configs.openscad_lsp")

return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        openscad_lsp = openscad_lsp.default_config,
      },
    },
  },
}
