from collections import deque


# Utilities
# =========

class Tree:
    def __init__(self, key):
        self.key = key
        self.children = []

def addword(T, word, fullword):
    if not word:
        T.key = T.key[0], fullword
        return

    wordstart = word[0].lower()

    for i, child in enumerate(T.children):
        char = child.key[0].lower()

        if wordstart == char:
            return addword(child, word[1:], fullword)

        if wordstart < char:
            newtree = Tree((wordstart, fullword if len(word) == 1 else None))
            T.children = T.children[:i] + [newtree] + T.children[i:]

            if not newtree.key[1]:
                addword(newtree, word[1:], fullword)

            return

    newtree = Tree((wordstart, fullword if len(word) == 1 else None))
    T.children.append(newtree)

    if not newtree.key[1]:
        addword(newtree, word[1:], fullword)


# Get data
# ========

try:
    with open('words.txt') as f:
        wordslist = f.read()
except:
    print('Unable to open words.txt; please download a wordlist and put it in ./words.txt.')
    print('Such a word list is available on GitHub: https://github.com/dwyl/english-words/blob/master/words.txt')

    # exit(1)
    wordslist = 'foo\nbar\nbaz\nblue'

words = wordslist.splitlines()

T = Tree(('', False))

for word in words:
    addword(T, word.strip(), word.strip())

sq = '\''


# Variables
# =========

# Arguments
r_word     = 'rdi' # 1
r_wordlen  = 'rsi' # 2
r_maxcost  = 'rdx' # 3

# Variables
r_bestword = 'rax'
r_bestcost = 'r13'
r_state    = 'rcx'
r_i        = 'r8'
r_cost     = 'r9'
r_stack    = 'r10'

# Temporary variables
r_char = 'r11b'
r_tmp  = 'r12'


# Code
# ====

with open('correctt.S', 'w') as f:
    f.write('''
    .intel_syntax noprefix

    .data
''')

    # Write word table
    maxlen = len(max(words, key=len))

    for word in words:
        sp = ' ' * (maxlen - len(word) + 1)
        f.write(f'''W{word.replace("'", '_')}{sp}: .asciz "{word}"\n''')

    # Write intro
    f.write(f'''

    .text

.macro stpush nextstate, ch
        # Increase cost unless the character is equal
        cmp     {r_char}, \\ch
        jne     1f

        push    {r_cost}
        jmp     2f

        # Although if the cost is too large, we ain't doing that,
        # instead directly going to the next state
1:      cmp     {r_cost}, {r_maxcost}
        jae     4f

        push    {r_cost}
        add     {r_cost}, 1

        # Push next state (next instruction to execute, plus current char and cost)
2:      .att_syntax
        lea     3f(%rip), %{r_tmp}
        .intel_syntax noprefix

        push    {r_tmp}
        push    {r_i}

        # Advance to next character
        add     {r_i}, 1

        # Jump to given state
        jmp     \\nextstate

3:      mov     {r_char}, BYTE PTR [{r_word}+{r_i}]
4:
.endm

.macro wordend word, len
        # Get cost (cost + abs(len - i))
        # https://stackoverflow.com/a/2639219
        mov     r14, \\len
        mov     {r_tmp}, {r_wordlen}
        sub     {r_tmp}, r14
        sub     r14, {r_wordlen}
        cmovg   {r_tmp}, r14
        add     {r_tmp}, {r_cost}

        # If cost is lower than best cost till now, save it
        cmp     {r_tmp}, {r_bestcost}
        jg      1f

        mov     {r_bestcost}, {r_tmp}

        .att_syntax
        lea     \\word(%rip), %{r_bestword}
        .intel_syntax noprefix

        # If cost is zero, return immediately
        cmp     {r_tmp}, 0
        je      .end

1:
.endm


    .globl  correct

correct:
        # Save registers
        push    rbx
        push    rbp
        push    r12
        push    r13
        push    r14

        # Initialize variables
        mov     {r_i}, 0
        mov     {r_cost}, 0
        mov     {r_stack}, rsp
        mov     {r_bestword}, {r_word}
        mov     {r_bestcost}, {r_maxcost}

        jmp     .start

.inputend:
.stpop:
        # Make sure we can pop; if we can't, return
        cmp     {r_stack}, rsp
        je      .end

        # Pop saved state
        pop     {r_i}
        pop     {r_tmp}
        pop     {r_cost}

        # Jump to next possibility
        jmp     {r_tmp}

.end:
        # Restore stack and registers
        mov     rsp, {r_stack}

        pop    r14
        pop    r13
        pop    r12
        pop    rbp
        pop    rbx
    
        # Return
        ret

.start:

''')


    # Meat of the subject
    i = 0
    Q = deque([ ('', 0, T) ])

    while len(Q):
        prefix, state, node = Q.popleft()
        ch, is_end = node.key

        prefix += ch
        sp = ' ' * (6 - len(str(state)))

        f.write(f'.S{state}:{sp}  # \'{prefix}\'\n')

        if is_end:
            # Save state if we reached the end of this path
            f.write(f'''        wordend W{is_end.replace("'", '_')}, {len(is_end)}\n\n''')

        # Write case where we're at the end of the string
        f.write(f'        mov     {r_char}, BYTE PTR [{r_word}+{r_i}]\n\n')

        f.write(f'        cmp     {r_char}, 0\n')
        f.write(f'        je      .inputend\n\n')

        # Write jumps to children
        states = []

        for j, child in enumerate(node.children):
            i += 1
            childstate = i

            states.append(childstate)

            f.write(f'        stpush  .S{childstate}, \'{child.key[0]}\'\n')

            Q.append((prefix, childstate, child))

        # End of loop, pop (which fails if needed)
        f.write(f'        jmp     .stpop\n\n')
