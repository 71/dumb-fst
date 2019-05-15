#include "correct.h"

#include <stdio.h>
#include <string.h>

int main(int argc, char** argv) {
    for (int i = 1; i < argc; i++) {
        char* suggestion = correct(argv[i], strlen(argv[i]), 2);

        puts(suggestion);
    }

    return 0;
}
