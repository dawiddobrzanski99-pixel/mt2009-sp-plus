
BEGIN {
    split("28537 28531 28500 28533 28535 28508 28512 28543 28540",a," ")
    for (i in a) ids[a[i]]=1
    inside=0
}
$1=="section" {
    if (inside) exit 2
    inside=1
    skip=0
    block=$0 ORS
    next
}
inside {
    block=block $0 ORS
    if ($1=="reward" && ($2 in ids)) skip=1
    if ($1=="end") {
        if (!skip) printf "%s",block
        inside=0
    }
    next
}
{ print }
END { if (inside) exit 2 }
