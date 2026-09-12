# Valorant-BanpickBot

## Version 1.0.0

VALORANTのチーム戦でBan/Pickを行う際の案内をしてくれるBotです

## How to use

`source/bot.py` をローカル環境へ取得して実行してください。
Python 3.10以上と、Discord Developer Portalで作成したBotアカウントが必要です。

### 初回セットアップ

リポジトリのルートで以下を実行します。

```powershell
python -m pip install -r source/requirements.txt
```

Discord Developer PortalのBot設定で、Privileged Gateway Intentsの
**Message Content Intent**を有効にしてください。

### トークン設定

`source/bot.py` の `DISCORD_TOKEN` にBotトークンを入力するか、環境変数で設定します。
トークンを入力したファイルはGitへコミット・公開しないでください。

PowerShellの場合：

```powershell
$env:DISCORD_TOKEN="Botトークン"
python source/bot.py
```

### マッププールの変更

`source/bot.py` の `MAP_POOL` を編集してください。
マップ名の並び順が、Botで表示される番号になります。

```python
MAP_POOL = (
	"ASCENT",
	"SPLIT",
	"LOTUS",
	"FRACTURE",
	"HAVEN",
	"ICEBOX",
	"PEARL",
)
```

マッププールは7個固定です。追加・削除・並び順の変更後はBotを再起動してください。

### コマンド

```text
!dice       1から100のダイスを振る
!maplist    マップ一覧を表示する
!bp1        BO1を開始する
!bp3        BO3を開始する
!bp5        BO5を開始する
!bpcancel   進行中のバンピックをキャンセルする
```
