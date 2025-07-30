def circle_matchings(n):
    # standard “pivot + circle” 1-factorization
    pivot, circle = n-1, list(range(n-1))
    weeks = n-1
    m = {}
    for w in range(1, weeks+1):
        ms = [(pivot, circle[w-1])]
        for k in range(1, n//2):
            i = circle[(w-1 + k) % (n-1)]
            j = circle[(w-1 - k) % (n-1)]
            ms.append((i,j))
        m[w-1] = ms
    return m

