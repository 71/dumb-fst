CC      =gcc
CFLAGS  =-Wall -Wextra -Werror -pedantic -std=c99 -O3

SRC=main.c correct.S
OBJ=main.o correct.o


all: main

main: $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^

main.o: main.c
	$(CC) $(CFLAGS) -c $^ -o $@

correct.o: correct.S
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: clean

clean:
	-rm -f *.o
	-rm -f *.exe
	-rm -f main
