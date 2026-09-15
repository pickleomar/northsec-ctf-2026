
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

void win(){
    system("cat flag.txt");
}

struct frame {
    char input[16];
    char number_buf[16];
    char *correct;
    char *dest;
};

void challenge() {

    struct frame f;

    puts("=== welcome to your childhood game ===");

    for (int i = 1; i <= 30; i++) {

        if (i % 5 == 0) {
            f.correct = "boom";
        } else {
            snprintf(f.number_buf, sizeof(f.number_buf), "%d", i);
            f.correct = f.number_buf;
        }

        printf("[%d] > ", i);


        read(0, f.input, 0x50);

        printf("You said: %s\n", f.input);

        f.input[15] = 0;

        f.dest = f.input;

        strcpy(f.dest, f.correct);

        printf("Correct: %s\n", f.dest);
    }
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    challenge();
    return 0;
}
