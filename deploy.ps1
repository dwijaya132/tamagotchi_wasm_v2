param([string]$msg = "update app")

$env:PYTHONUTF8 = 1
git add .
git commit -m $msg
git push
pygbag --build --template custom.tmpl .
wrangler pages deploy build/web --project-name=tamagotchi-wasm-v2