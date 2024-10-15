require("mason").setup()
require("mason-lspconfig").setup()

require("lspconfig").ts_ls.setup({})
require("lspconfig").biome.setup({})
