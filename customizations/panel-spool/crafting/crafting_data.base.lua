CRAFTING_BLACKSMITH = 101
CRAFTING_BAEKGO = 102
CRAFTING_CHEF = 103
CRAFTING_HALFDEMON = 104
CRAFTING_HORSEMAN = 105
CRAFTING_ARROW = 106
CRAFTING_BLACK_STEEL = 107
CRAFTING_NAKAJIMA = 108
CRAFTING_ALCHEMIST_ORE = 109
CRAFTING_BUM = 110
CRAFTING_URIEL = 111

ITEM_CRAFT_CHANGE_ATTR_INDEX = 101

crafting_data = {
    [CRAFTING_BLACKSMITH] = {
        1,2,3,4,5,6
    },

    [CRAFTING_BAEKGO] = {
        11, 12, 13, 14, 15, 16, 17,
        18, 19, 20, 21, 22, 23, 24,
        25, 26, 27, 28, 29, 30, 31,
        32, 33, 34, 35, 36, 37, 38,
        39, 40, 41, 42, 43, 44, 45,
        46, 47, 48, 49, 50, 51, 52,
        53, 54, 55, 56, 57,
        --[[58, 59,
        60, 61, 62, 63, 64, 65, 66,]] -- wszystkie rosy pvp
        67, 68, 71, 72, 73, 74, 78,
        79, 80, 81, 82, 83, 84, 85,
        86, 87, 88, 92, 93, 94, 95,
    },

    [CRAFTING_CHEF] = {
        90, 91
    },

    [CRAFTING_HALFDEMON] = {
        100, 101, 102, 103
    },

    [CRAFTING_HORSEMAN] = {
        151, 152
    },

    [CRAFTING_ARROW] = {
        8001, 8002, 8003, 8004, 8005
    },

    [CRAFTING_BLACK_STEEL] = {
        201, 202, 203, 204
    },

    [CRAFTING_NAKAJIMA] = {
        301, 302, 303
    },

    [CRAFTING_ALCHEMIST_ORE] = {
        351, 352, 353, 354,
        355, 356, 357, 358,
        359, 360, 361, 362
    },

    [CRAFTING_BUM] = { 221 },
    [CRAFTING_URIEL] = { 85001 },

    -- guild alchemist
    [20060] = {50621, 50635, 50636, 50637, 50638},
    [20062] = {50623, 50635, 50636, 50637, 50638},
    [20063] = {50624, 50635, 50636, 50637, 50638},
    [20064] = {50625, 50635, 50636, 50637, 50638},
    [20065] = {50626, 50635, 50636, 50637, 50638},
    [20066] = {50627, 50635, 50636, 50637, 50638},
    [20067] = {50628, 50635, 50636, 50637, 50638},
    [20068] = {50629, 50635, 50636, 50637, 50638},
    [20069] = {50630, 50635, 50636, 50637, 50638},
    [20070] = {50631, 50635, 50636, 50637, 50638},
    [20071] = {50632, 50635, 50636, 50637, 50638},
    [20072] = {50633, 50635, 50636, 50637, 50638},
}

local function GetCraftingData(vnum)
    local item_vnum, count, price, chance, req_progress, req_min_level, recipe_vnum = get_crafting_data(vnum)
    local recipe_items = {get_crafting_recipe(vnum)}
    local craft_price = math.max(price, game.get_event_flag("crafting_price"..vnum))
    local is_guild_crafting = vnum >= 50621 and vnum <= 50638 -- przetopy
    return {
        item_vnum = item_vnum,
        count = count,
        price = craft_price,
        chance = chance,
        recipe = recipe_items,
        requirements = {
            progress = {
                vnum = recipe_vnum,
                max = req_progress
            },
            min_level = req_min_level
        },
        is_guild = is_guild_crafting
    }
end

crafting_data.get_data = GetCraftingData-- CUSTOM_UKRAINKA_CRAFTING_V1
-- Move only the selected exchanges; retain other NPC recipes.
for _, recipes in pairs(crafting_data) do
    if type(recipes) == "table" then
        for i = table.getn(recipes), 1, -1 do
            local id = recipes[i]
            if id == 100 or id == 101 or id == 104 then
                table.remove(recipes, i)
            end
        end
    end
end
crafting_data[30099] = {100, 101, 104}
