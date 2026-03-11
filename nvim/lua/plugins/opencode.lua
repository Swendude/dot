return {
  "nickjvandyke/opencode.nvim",
  version = "*", -- Latest stable release
  dependencies = {
    {
      -- `snacks.nvim` integration is recommended, but optional
      ---@module "snacks" <- Loads `snacks.nvim` types for configuration intellisense
      "folke/snacks.nvim",
      optional = true,
      opts = {
        input = {}, -- Enhances `ask()`
        picker = { -- Enhances `select()`
          actions = {
            opencode_send = function(...)
              return require("opencode").snacks_picker_send(...)
            end,
          },
          win = {
            input = {
              keys = {
                ["<leader>aa"] = { "opencode_send", mode = { "n", "i" } },
              },
            },
          },
        },
      },
    },
  },
  config = function()
    ---@type opencode.Opts
    vim.g.opencode_opts = {
      -- Your configuration, if any; goto definition on the type or field for details
    }

    vim.o.autoread = true -- Required for `opts.events.reload`

    -- Recommended/example keymaps
    vim.keymap.set({ "n", "x" }, "<leader>aa", function()
      require("opencode").ask("@this: ", { submit = true })
    end, { desc = "Ask opencode…" })
    vim.keymap.set({ "n", "x" }, "<leader>ax", function()
      require("opencode").select()
    end, { desc = "Execute opencode action…" })
    vim.keymap.set({ "n", "t" }, "<leader>at", function()
      require("opencode").toggle()
    end, { desc = "Toggle opencode" })

    vim.keymap.set("n", "<leader>a", "<nop>", { desc = "Opencode" })

    vim.keymap.set({ "n", "x" }, "<leader>ao", function()
      return require("opencode").operator("@this ")
    end, { desc = "Add range to opencode", expr = true })
    vim.keymap.set("n", "<leader>aO", function()
      return require("opencode").operator("@this ") .. "_"
    end, { desc = "Add line to opencode", expr = true })

    vim.keymap.set("n", "<leader>au", function()
      require("opencode").command("session.half.page.up")
    end, { desc = "Scroll opencode up" })
    vim.keymap.set("n", "<leader>ad", function()
      require("opencode").command("session.half.page.down")
    end, { desc = "Scroll opencode down" })

    local ok, wk = pcall(require, "which-key")
    if ok then
      wk.add({
        { "<leader>a", group = "opencode" },
        { "<leader>aa", desc = "Ask opencode…" },
        { "<leader>ax", desc = "Execute opencode action…" },
        { "<leader>at", desc = "Toggle opencode" },
        { "<leader>ao", desc = "Add range to opencode" },
        { "<leader>aO", desc = "Add line to opencode" },
        { "<leader>au", desc = "Scroll opencode up" },
        { "<leader>ad", desc = "Scroll opencode down" },
      })
    end
  end,
}
