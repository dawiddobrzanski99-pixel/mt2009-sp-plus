import ui
import app
import player
import eventManager
import time
import localeInfo
import updateable

from ui_event import Event

class WorldBossData:
    def __init__(self, vnum):
        self.vnum = vnum
        self.alive = False
        self.respawn_time = 0
        self.ranking = []
        self.personal = None

    def update_day_info(self, alive, respawn_time):
        self.alive = alive
        self.respawn_time = respawn_time

    def add_ranking_entry(self, rank, name, damage, timestamp):
        self.ranking.append({
            "rank": rank,
            "name": name,
            "damage": damage,
            "timestamp": timestamp
        })

    def set_personal_entry(self, name, damage, timestamp):
        self.personal = {
            "name": name,
            "damage": damage,
            "timestamp": timestamp
        }

    def clear_ranking(self):
        del self.ranking[:]

        self.personal = None

class WorldBossController(ui.SimplyWindow):
    def __init__(self, *args, **kwargs):
        super(WorldBossController, self).__init__(
            "UI", ("movable", "float"),
            645, 375,
            self.__Initialize, self.__Destroy
        )

    def __Initialize(self):
        self.windowConfig["user-defines"] = {
            "data" : {}
        }
        self.SetSize(*self.windowConfig["size"].values())

        board = self.__CreateBoard()
        self.tab = self.__CreateTabs(board)
        self.renderTarget = self.__CreateRenderTarget(board)

        right_panel_x = self.renderTarget.GetLocalPosition()[0] + self.renderTarget.GetWidth() - 1
        self.headers, self.dungeonImage = self.__CreateHeaders(right_panel_x, board)
        self.__CreateInfoBoxes(right_panel_x, board, self.headers[2], self.dungeonImage)

        self.AppendObject("data", (self.renderTarget, self.headers, self.dungeonImage))

        eventManager.EventManager().add_observer("WORLD_BOSS_REGISTER_DAY", self.__RegisterDay)
        eventManager.EventManager().add_observer("WORLD_BOSS_REGISTER_RANKING", self.__RegisterRanking)
        eventManager.EventManager().add_observer("WORLD_BOSS_REGISTER_PERSONAL", self.__RegisterPersonal)

    def __Destroy(self):
        pass

    def Open(self):
        super(WorldBossController, self).Open()
        self.__Refresh()

    def Close(self):
        super(WorldBossController, self).Close()

    def OnKeyDown(self, key):
        if key == app.VK_ESCAPE:
            self.Close()
            return True
        return False

    def __CreateBoard(self):
        board = ui.BoardWithTitleBar()
        board.SetParent(self)
        board.SetPosition(0, 0)
        board.SetSize(*self.GetSize())
        board.SetTitleName("World Boss")
        board.SetCloseEvent(Event(self.Close))
        board.Show()
        self.AppendObject("board", board)
        return board

    def __CreateTabs(self, parent):
        tab = ui.TabBoard()
        tab.SetParent(parent)
        tab.SetPosition(10, 30)
        tab.SetSize(parent.GetWidth(), 33)
        tab.SetTabWidth(89)
        tab.SetVisual(
            "Assets/ui/world-boss/button-tab-0.png",
            "Assets/ui/world-boss/button-tab-1.png",
            "Assets/ui/world-boss/button-tab-1.png"
        )
        tab.Show()

        self.day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(self.day_names):
            tab.AppendTab(day)
            tab.SetTabEvent(day, Event(self.__RequestData, i))

        self.AppendObject("tab", tab)
        return tab

    def __CreateRenderTarget(self, parent):
        tab = self.GetObject("tab")
        renderTarget = ui.RenderTarget()
        renderTarget.SetParent(parent)
        renderTarget.SetPosition(tab.GetLocalPosition()[0], tab.GetLocalPosition()[1] + tab.GetHeight() + 2)
        renderTarget.SetSize(298, 299)
        renderTarget.SetRenderTarget(5)
        renderTarget.Show()
        return renderTarget

    def __CreateHeaders(self, x, parent):
        headers = [ui.TransparentButton() for _ in range(3)]

        headers[0].SetParent(parent)
        headers[0].SetPosition(x, self.tab.GetLocalPosition()[1] + self.tab.GetHeight())
        headers[0].SetUpVisual("Assets/ui/world-boss/header-up.png")
        headers[0].Show()
        headers[0].SetText("Boss Info")

        image = ui.ImageBox()
        image.SetParent(parent)
        image.SetPosition(x, headers[0].GetLocalPosition()[1] + headers[0].GetHeight() + 3)
        image.LoadImage("Assets/ui/world-boss/dungeon-image.png")
        image.Show()

        headers[1].SetParent(parent)
        headers[1].SetPosition(x, image.GetLocalPosition()[1] + image.GetHeight() + 3)
        headers[1].SetUpVisual("Assets/ui/world-boss/header-status.png")
        headers[1].Show()
        headers[1].SetText("Status")

        headers[2].SetParent(parent)
        headers[2].SetPosition(x + headers[1].GetWidth(), headers[1].GetLocalPosition()[1])
        headers[2].SetUpVisual("Assets/ui/world-boss/header-ranking.png")
        headers[2].Show()
        headers[2].SetText("Ranking")

        return headers, image

    def __CreateInfoBoxes(self, x, parent, header_ranking, image):
        y_pos = header_ranking.GetLocalPosition()[1] + header_ranking.GetHeight()

        box_status = ui.MakeImageBox(parent, "Assets/ui/world-boss/background-status.png", x, y_pos)
        self.AppendObject("boxes", box_status, True)

        self.status_images = []
        self.status_texts = []

        for i in range(2):
            img = ui.ImageBox()
            img.SetParent(box_status)
            img.LoadImage("Assets/ui/world-boss/input-status.png")
            img.SetPosition(0, 10 + i * 35)
            img.SetWindowHorizontalAlignCenter()
            img.Show()
            self.status_images.append(img)

        labels = ["Status: ", "", "Time: ", ""]
        for i in range(4):
            line = ui.TextLine()
            line.SetParent(self.status_images[i // 2])
            line.SetPosition(5 if i % 2 == 0 else 0, 0)
            line.SetText(labels[i])
            if i % 2 == 1:
                line.SetWindowHorizontalAlignRight()
                line.SetHorizontalAlignRight()
            line.SetWindowVerticalAlignCenter()
            line.SetVerticalAlignCenter()
            line.Show()
            self.status_texts.append(line)

        self.AppendObject("status-data", (self.status_images, self.status_texts))

        teleport_btn = ui.Button()
        teleport_btn.SetParent(box_status)
        teleport_btn.SetPosition(0, 38)
        teleport_btn.SetUpVisual("Assets/ui/world-boss/button-teleport-0.png")
        teleport_btn.SetOverVisual("Assets/ui/world-boss/button-teleport-0.png")
        teleport_btn.SetDownVisual("Assets/ui/world-boss/button-teleport-0.png")
        teleport_btn.SetText("Teleport")
        teleport_btn.SetWindowHorizontalAlignCenter()
        teleport_btn.SetWindowVerticalAlignBottom()
        teleport_btn.Show()
        self.AppendObject("teleport-button", teleport_btn)

        x_pos_next = x + box_status.GetWidth()
        box_ranking = ui.MakeImageBox(parent, "Assets/ui/world-boss/background-ranking.png", x_pos_next, y_pos)
        self.AppendObject("boxes", box_ranking)

        rank_img = ui.ImageBox()
        rank_img.SetParent(box_ranking)
        rank_img.SetPosition(0, 10)
        rank_img.LoadImage("Assets/ui/world-boss/ranking-rows.png")
        rank_img.SetWindowHorizontalAlignCenter()
        rank_img.Show()
        self.AppendObject("ranking-image", rank_img)

        self.ranking_lines = []

        for i in range(5):
            line = ui.TextLine()
            line.SetParent(rank_img)
            line.SetPosition(45, 2 + i * 20)
            line.SetText("")
            line.Show()
            self.ranking_lines.append(line)

        self.AppendObject("ranking-lines", self.ranking_lines)

    def __RequestData(self, day_index):
        self.__UpdateDungeonImage(day_index)
        if day_index not in self.windowConfig["user-defines"]["data"]:
            return

        entries = list(self.windowConfig["user-defines"]["data"][day_index].values())
        if not entries:
            return

        self.__DisplayEntry(entries[0])

    def __Refresh(self):
        player.SetBackground(5, "Assets/ui/world-boss/background-render.png")
        player.SetVisibility(5, True)
        self.__RequestData(0)

    def __UpdateStatusInfo(self, status_text, time_text):
        self.status_texts[1].SetText(status_text)
        self.status_texts[3].SetText(time_text)

    def __UpdateDungeonImage(self, index):
        # Przykładowa rotacja obrazków dungeonów
        dungeon_images = [
            "Assets/ui/world-boss/dungeon-image.png",
            "Assets/ui/world-boss/dungeon-image.png",
            "Assets/ui/world-boss/dungeon-image.png",
            "Assets/ui/world-boss/dungeon-image.png",
            "Assets/ui/world-boss/dungeon-image.png",
            "Assets/ui/world-boss/dungeon-image.png",
            "Assets/ui/world-boss/dungeon-image.png",
        ]
        self.dungeonImage.LoadImage(dungeon_images[index % len(dungeon_images)])

    def __ConvertDayIndexFromServer(self, server_day_index):
        return (server_day_index - 1) % 7

    def __RegisterDay(self, server_day_index, vnum, is_alive, next_spawn_time):
        sys_err("A", [server_day_index, vnum, is_alive, next_spawn_time])
        day_index = self.__ConvertDayIndexFromServer(server_day_index)
        if day_index not in self.windowConfig["user-defines"]["data"]:
            self.windowConfig["user-defines"]["data"][day_index] = {}

        if vnum not in self.windowConfig["user-defines"]["data"][day_index]:
            self.windowConfig["user-defines"]["data"][day_index][vnum] = WorldBossData(vnum)

        boss = self.windowConfig["user-defines"]["data"][day_index][vnum]
        boss.update_day_info(is_alive, next_spawn_time)
        boss.clear_ranking()

        if self.tab.GetSelectedTabIndex() == day_index:
            self.__RequestData(day_index)

    def __RegisterRanking(self, server_day_index, vnum, rank, name, damage, timestamp):
        day_index = self.__ConvertDayIndexFromServer(server_day_index)
        if day_index in self.windowConfig["user-defines"]["data"] and vnum in self.windowConfig["user-defines"]["data"][day_index]:
            self.windowConfig["user-defines"]["data"][day_index][vnum].add_ranking_entry(rank, name, damage, timestamp)

    def __RegisterPersonal(self, server_day_index, vnum, name, damage, timestamp):
        day_index = self.__ConvertDayIndexFromServer(server_day_index)
        if day_index in self.windowConfig["user-defines"]["data"] and vnum in self.windowConfig["user-defines"]["data"][day_index]:
            self.windowConfig["user-defines"]["data"][day_index][vnum].set_personal_entry(name, damage, timestamp)

    def __DisplayEntry(self, boss):
        self.current_boss = boss

        if boss.alive:
            alive_text = "Alive"
            time_text = "Now"
        else:
            alive_text = "Dead"
            self.respawn_seconds_remaining = app.GetTime() + boss.respawn_time
            time_text = localeInfo.sec2time(self.respawn_seconds_remaining, "DHMS")

        self.__UpdateStatusInfo(alive_text, time_text)
        player.SelectModel(5, boss.vnum)
        self.__UpdateRanking(boss)            

    def OnUpdate(self):
        if self.respawn_seconds_remaining - app.GetTime() > 0:
            self.status_texts[3].SetText(localeInfo.sec2time(self.respawn_seconds_remaining - app.GetTime(), "DHMS"))
        else:
            self.status_texts[1].SetText("Alive")
            self.status_texts[3].SetText("Now")

    def __UpdateRanking(self, boss):
        print("--- Ranking ---")
        sys_err(boss.ranking)
        ranking_lines = self.GetObject("ranking-lines")
        for line, entry in zip(ranking_lines, boss.ranking):
            line.SetText("{} - {}".format(entry['name'], entry['damage']))

        # Clear remaining lines if ranking has fewer than 5 entries
        for line in ranking_lines[len(boss.ranking):]:
            line.SetText("")

    def __FormatRespawnTime(self, timestamp):
        """
        Zwraca sformatowany czas z timestampu.
        """
        return time.strftime("%H:%M:%S", time.localtime(timestamp))