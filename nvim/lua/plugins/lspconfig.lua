return {
  "neovim/nvim-lspconfig",
  opts = {
    inlay_hints = { enabled = false },
    servers = {
      yamlls = {
        settings = {
          yaml = {
            format = {
              singleQuote = true,
            },
          },
        },
      },
    },
  },
}
