Zero-alloc dumb [Levenshtein automaton](https://en.wikipedia.org/wiki/Levenshtein_automaton).

- Uses a [Python 3.7 script](./generate-correct.py) to generate a [`correct.S`](./correct.S)
  file, which defines the entire automaton statically in x86.
- First match is naively returned.
- Additions and removals are not handled; only differences in characters are checked.

## But why?

As a part of [Epita](https://epita.fr)'s curriculum, we had to make an OCR in C.
Bonus points for any sort of text correction.

I was bored, and I don't like using `alloc` / `free` / etc in C,
so I set out to generate an automaton that would do correct
some invalid words without allocating anything.

## History

This was originally part of another (private) repository, which is why no commit
history is available. However, here are some highlights:

- At first, I generated C code and did not share common string prefixes between
  states of the automaton. This led to an impressive 78.8 MBs `correct.c` file
  with 4,865,443 lines of code. Of all the compilers I tried (`tcc`, `gcc`, `clang`, `msvc`),
  only `tcc` was able to compile that piece of code. However, the program would
  instantly crash when it was opened.
- Then, I started generating x86 code instead, in order to have better control
  over things.
- Finally, I made sure redundant states were shared between prefixes and used a
  lot of macros. Now everything kinda works.

The automaton is still very dumb though, so don't expect magical things from it.

I'm mostly publishing it online because I had fun making it, and I think it was
an interesting exercise.

## Assembly code

Here is a snippet of code when the words `bar` and `baz` are part of the dictionary.

```assembly
.S3:     # 'ba'

  # This is not a complete word, so we simply try to move on to the next character.
  mov     r11b, BYTE PTR [rdi+r8]

  # Cancel if the end of the input has been reached.
  cmp     r11b, 0
  je      .inputend

  # Try to match 'ba' + 'r', and save 'bar' if it works (or if the distance is
  # below the given threshold).
  stpush  .S6, 'r'

  # Same with 'ba' + 'z'.
  stpush  .S7, 'z'

  # Move on to next possibility.
  jmp     .stpop


.S6:     # 'bar'

  # Test if the end has been reached, which means our input word matches 'bar'.
  wordend Wbar, 3

  mov     r11b, BYTE PTR [rdi+r8]

  # Cancel if the end of the input has been reached.
  cmp     r11b, 0
  je      .inputend

  # Move on to next possibility.
  jmp     .stpop


.S7:     # 'baz'

  # Same as above.
  wordend Wbaz, 3

  mov     r11b, BYTE PTR [rdi+r8]

  cmp     r11b, 0
  je      .inputend

  jmp     .stpop
```
