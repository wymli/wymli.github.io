
publish:
    #!/usr/bin/bash
    hugo build
    git add .
    git commit -m "update"
    git push