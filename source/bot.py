import os
import random
from dataclasses import dataclass, field

import discord


MAP_POOL = (
    "ASCENT",
    "SPLIT",
    "LOTUS",
    "FRACTURE",
    "HAVEN",
    "ICEBOX",
    "PEARL",
)

ATTACKER = 1
DEFENDER = 2


@dataclass
class Step:
    team: str
    action: str
    map_number: int | None = None


@dataclass
class Match:
    best_of: int
    channel_id: int
    team_a: int
    team_b: int | None = None
    steps: list[Step] = field(default_factory=list)
    step_index: int = 0
    available_maps: set[int] = field(default_factory=lambda: set(range(1, len(MAP_POOL) + 1)))
    selected_maps: dict[int, dict[str, object]] = field(default_factory=dict)
    dice_a: int = 0
    dice_b: int = 0
    team_choice_pending: bool = True

    @property
    def current_step(self) -> Step | None:
        if self.step_index >= len(self.steps):
            return None
        return self.steps[self.step_index]


def build_steps(best_of: int) -> list[Step]:
    if best_of == 1:
        steps = [Step("A", "BAN"), Step("B", "BAN")]
        steps.extend(Step("A" if index % 2 == 0 else "B", "BAN") for index in range(4))
        steps.append(Step("A", "SIDE"))
        return steps

    if best_of == 3:
        return [
            Step("A", "BAN"),
            Step("B", "BAN"),
            Step("A", "PICK", 1),
            Step("B", "SIDE", 1),
            Step("B", "PICK", 2),
            Step("A", "SIDE", 2),
            Step("A", "BAN"),
            Step("B", "BAN"),
            Step("A", "SIDE", 3),
        ]

    return [
        Step("A", "BAN"),
        Step("B", "BAN"),
        Step("A", "PICK", 1),
        Step("B", "SIDE", 1),
        Step("B", "PICK", 2),
        Step("A", "SIDE", 2),
        Step("A", "PICK", 3),
        Step("B", "SIDE", 3),
        Step("B", "PICK", 4),
        Step("A", "SIDE", 4),
        Step("B", "SIDE", 5),
    ]


def format_maps(match: Match) -> str:
    return "\n".join(
        f"{index}: {MAP_POOL[index - 1]}"
        + ("" if index in match.available_maps else " (BAN済み)")
        for index in range(1, len(MAP_POOL) + 1)
    )


def side_name(value: int) -> str:
    return "ATTACKER" if value == ATTACKER else "DEFENDER"


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
matches: dict[int, Match] = {}


async def send_step_prompt(message: discord.Message, match: Match) -> None:
    step = match.current_step
    if step is None:
        await finish_match(message, match)
        return

    if step.action in {"BAN", "PICK"}:
        action_text = "BAN" if step.action == "BAN" else f"マップ{step.map_number}として選択"
        await message.channel.send(
            f"【マップ：{action_text}】\n{format_maps(match)}\n\n"
            f"チーム{step.team}は番号を入力してください。"
        )
        return

    await message.channel.send(
        f"【マップ{step.map_number}：攻守選択】\n"
        "1: ATTACKER\n"
        "2: DEFENDER\n\n"
        f"チーム{step.team}は番号を入力してください。"
    )


async def finish_match(message: discord.Message, match: Match) -> None:
    lines = ["BAN&PICKを終了します。"]
    for map_number in sorted(match.selected_maps):
        result = match.selected_maps[map_number]
        lines.append(f"\n【第{map_number}マップ】")
        lines.append(f"** {result['map']} **")
        lines.append(f"チーム{result['side_team']}の選択陣営： ** {side_name(result['side'])} **")

    await message.channel.send("\n".join(lines))
    matches.pop(match.channel_id, None)


def representative_id(match: Match, team: str) -> int | None:
    return match.team_a if team == "A" else match.team_b


@client.event
async def on_ready() -> None:
    print(f"起動しました: {client.user}")


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user:
        return

    content = message.content.strip()
    channel_id = message.channel.id

    if content == "!dice":
        await message.channel.send(f"ダイスの目は「{random.randint(1, 100)}」です。")
        return

    if content == "!maplist":
        await message.channel.send("【マップ一覧】\n" + "\n".join(
            f"{index}: {map_name}" for index, map_name in enumerate(MAP_POOL, start=1)
        ))
        return

    if content == "!bpcancel":
        match = matches.get(channel_id)
        if match is None:
            await message.channel.send("進行中のバンピックはありません。")
            return
        if message.author.id not in {match.team_a, match.team_b}:
            await message.channel.send("このコマンドは代表者のみ実行できます。")
            return
        matches.pop(channel_id, None)
        await message.channel.send("バンピックをキャンセルしました。")
        return

    if content in {"!bp1", "!bp3", "!bp5"}:
        if channel_id in matches:
            await message.channel.send("このチャンネルでは現在バンピックが進行中です。")
            return
        if len(MAP_POOL) != 7:
            await message.channel.send("MAP_POOLは7個に設定してください。")
            return

        best_of = int(content[-1])
        match = Match(
            best_of=best_of,
            channel_id=channel_id,
            team_a=message.author.id,
            steps=build_steps(best_of),
        )
        matches[channel_id] = match
        match.dice_a = random.randint(1, 100)
        match.dice_b = random.randint(1, 100)
        while match.dice_a == match.dice_b:
            match.dice_a = random.randint(1, 100)
            match.dice_b = random.randint(1, 100)

        await message.channel.send(
            f"BO{best_of}のバンピックを開始します。\n"
            f"チームA代表者: <@{match.team_a}>\n"
            f"ダイス結果: A={match.dice_a}, B={match.dice_b}\n"
            f"ダイス勝者はチームA/Bのどちらを担当するか入力してください。"
        )
        return

    match = matches.get(channel_id)
    if match is None:
        return

    if match.team_choice_pending:
        if message.author.id != match.team_a or content not in {"A", "B"}:
            await message.channel.send("チームA代表者は A または B を入力してください。")
            return
        match.team_choice_pending = False
        await message.channel.send(f"チーム{content}を選択しました。")
        await send_step_prompt(message, match)
        return

    if not content.isdigit():
        return

    step = match.current_step
    if step is None:
        await finish_match(message, match)
        return

    expected_user = representative_id(match, step.team)
    if expected_user is None:
        if step.team == "B" and content.isdigit() and int(content) in match.available_maps:
            match.team_b = message.author.id
            expected_user = match.team_b
        else:
            await message.channel.send("チームB代表者は、最初の有効な番号を入力してください。")
            return

    if message.author.id != expected_user:
        await message.channel.send("現在操作するチームの代表者以外は入力できません。")
        return

    value = int(content)
    if step.action in {"BAN", "PICK"}:
        if value not in match.available_maps:
            await message.channel.send("その番号は選択できません。表示されている番号を入力してください。")
            return
        selected_map = MAP_POOL[value - 1]
        match.available_maps.remove(value)
        if step.action == "PICK":
            match.selected_maps[step.map_number or 1] = {"map": selected_map}
        await message.channel.send(f"{selected_map}を{step.action}しました。")
    else:
        if value not in {ATTACKER, DEFENDER}:
            await message.channel.send("攻守は1または2で入力してください。")
            return
        map_number = step.map_number or 1
        remaining_map = min(match.available_maps)
        selected = match.selected_maps.setdefault(map_number, {"map": MAP_POOL[remaining_map - 1]})
        selected["side"] = value
        selected["side_team"] = step.team
        await message.channel.send(f"チーム{step.team}の陣営を{side_name(value)}にしました。")

    match.step_index += 1
    await send_step_prompt(message, match)


DISCORD_TOKEN = "ここにBotトークンを入力"
token = os.environ.get("DISCORD_TOKEN") or DISCORD_TOKEN
if not token:
    raise RuntimeError("環境変数DISCORD_TOKENを設定してください。")

client.run(token)