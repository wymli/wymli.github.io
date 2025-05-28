
alias p := publish
alias push := publish
publish:
    #!/usr/bin/bash
    hugo build
    git add .
    git commit -m "update"
    git push
    just update_readme


update_readme:
    #!/usr/bin/bash
    python x.py
    cd wymli
    git add .
    git commit -m "update"
    git push
    cd -

alias new := create
create $file $url:
    #!/usr/bin/bash
    d=$(date "+%Y-%m-%d")
    f="./content/posts/$file.md"
    echo $f
    cat > "$f" <<EOF
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

