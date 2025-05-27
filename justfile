
alias p := publish
alias push := publish
publish:
    #!/usr/bin/bash
    hugo build
    git add .
    git commit -m "update"
    git push

alias new := create
create $file $url:
    #!/usr/bin/bash
    d=$(date "+%Y-%m-%d")
    f="./content/posts/$file.md"
    cat > $f <<EOF
    ---
    title: "$file"
    date: "$d"
    tags: [""]
    categories: [""]
    ---

    <a href="$url" target="_blank"> 前往飞书云文档查看 </a>
    <iframe 
        width="100%"
        style="height: 80vh;"
        allow="fullscreen"
        src="$url">
    EOF
    code $f