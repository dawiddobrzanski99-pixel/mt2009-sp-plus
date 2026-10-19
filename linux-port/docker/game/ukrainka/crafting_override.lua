-- CUSTOM_UKRAINKA_CRAFTING_V1
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
